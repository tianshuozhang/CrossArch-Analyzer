from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import re
from core.function_parser_tool import FunctionParserTool


from core.state_manager import StateManager
from core.memory_manager import MemoryManager
from core.communication_bus import CommunicationBus, AgentMessage, MessageType
import uuid
from core.Static_CodeAnalyzer import Static_CodeAnalyzer

class EnhancedOrchestratorAgent:
    """增强的主控智能体：支持状态管理、记忆管理和多Agent协作"""
    
    def __init__(self, llm_config: Dict[str, Any], agent_id: str = "orchestrator_001"):
        self.agent_id = agent_id
        
        self.llm = ChatOpenAI(**llm_config)
        
        # 初始化核心工具
        
        self.static_classifier = Static_CodeAnalyzer()

        self.function_parser = FunctionParserTool()
        
        # 初始化增强组件
        self.state_manager = StateManager()
        # self.memory_manager = MemoryManager()
        self.memory_manager = MemoryManager(model_name="./LLM/models/all-MiniLM-L6-v2") # 使用本地模型

        self.communication_bus = CommunicationBus()            
        
        # 注册到通信总线
        self.communication_bus.register_agent(self.agent_id, self)
        
        # 当前状态
        self.current_state = {
            "agent_id": self.agent_id,
            "current_session": None,
            "conversation_history": [],
            "last_analysis_result": None,
            "last_analysis_result_nocode": None,
            "performance_metrics": {},
            "created_time": datetime.now().isoformat()
        }
        self.load_agent_state()
        self.load_agent_memories()
        # 系统提示词（支持上下文注入）
        self.system_prompt_template = """你是一个专业的代码架构分析引擎。你的任务是将C/C++代码按指令集架构分类。
        报告格式取决于用户请求。请根据用户请求的复杂程度，执行以下**条件指令**：

        **【模式 A：简要总结模式】**
        如果用户请求内容（如“总结一下”、“有哪些架构”、“简单说一下”）表明他们只需要**快速摘要或要点**：
        1.  你只需使用**自然语言文本**，简明扼要地总结主要发现。
        2.  **不需要**返回 JSON 格式的详细分析结果。

        **【模式 B：完整报告模式】**
        如果用户请求内容（如“完整的报告”、“详细分析”、“结构化输出”）表明他们需要**完整的架构依赖报告**：
        1.  首先，使用**自然语言文本**提供一个清晰、结构化的报告概览或表述。
        2.  **随后**，**使用分隔符 `---JSON_DATA---` 进行严格分隔**。
        3.  在分隔符之后，必须附带一个**完整的 JSON 格式数据块**，并使用 **Markdown 代码块标记 ` ```json` 和 ` ``` `** 进行封装。
            JSON 结构必须包括：
            - "architecture_summary": 架构依赖总结
            - "line_details": 每行代码的架构分类详情
            - "specific_patterns": 发现的架构特定代码模式
            - "compatibility_suggestions": 跨平台兼容性建议
            - "refactoring_suggestions": 重构建议（如需要）

        请**严格**确保分隔符 `---JSON_DATA---` **只出现一次**，并位于自然语言表述和 JSON 数据块之间。
"""
        
        # 注册消息处理器
        self._register_message_handlers()
        
    def _register_message_handlers(self):
        """注册消息处理器"""
        self.communication_bus.register_message_handler(
            MessageType.TASK_REQUEST, 
            self._handle_task_request
        )
        self.communication_bus.register_message_handler(
            MessageType.BROADCAST,
            self._handle_broadcast_message
        )
    
    def _build_context_window(self, code: str, file_path: str) -> str:
        """构建上下文窗口：将相关状态和记忆加载到LLM上下文[4](@ref)[8](@ref)"""
        
        context_parts = []
        
        # === 1. 关键信息前置：当前任务摘要（最高优先级）[6](@ref)[8](@ref) ===
        context_parts.append("【当前分析任务】")
        context_parts.append(f"文件路径: {file_path}")
        context_parts.append(f"代码规模: {len(code.splitlines())} 行代码")
        context_parts.append(f"分析目标: 识别代码中对特定指令集架构(如ARM, x86, RISC-V)的依赖")
        context_parts.append("###")  # 清晰的分隔符[7](@ref)
        
        # === 2. 动态记忆检索：基于当前代码内容的语义搜索[7](@ref) ===
        query_keywords = self._extract_arch_keywords(code)  # 从代码中提取架构相关关键词
        semantic_query = f"代码分析 {query_keywords} {file_path}"
        
        relevant_memories = self.memory_manager.retrieve_relevant_memories(
            semantic_query,  # 使用语义更丰富的查询
            memory_type="analysis_result",
            top_k=3  # 限制数量，保证相关性[5](@ref)
        )
        
        if relevant_memories:
            context_parts.append("【相关历史分析】")
            for i, memory in enumerate(relevant_memories[:3]):  # 最多2条最相关记忆
                context_parts.append(f"{i+1}. {memory.content}")
            context_parts.append("###")
        
        # === 3. 会话状态：上次分析结果（如果存在）===
        if self.current_state.get("last_analysis_result"):
            last_result = self.current_state["last_analysis_result"]
            arch_stats = last_result.get('summary', {}).get('architecture_statistics', {})
            
            context_parts.append("【上次分析架构分布】")
            for arch, count in arch_stats.items():
                if count > 0:  # 只显示有内容的架构
                    context_parts.append(f"- {arch}: {count} 行代码")
            context_parts.append("###")
        
        # === 4. 性能元数据（辅助LLM理解分析模式）===
        if self.current_state.get("performance_metrics"):
            metrics = self.current_state["performance_metrics"]
            context_parts.append("【分析模式参考】")
            
            # 只选择关键指标，避免信息过载
            key_metrics = {
                "平均分析时间": metrics.get("avg_analysis_time"),
                "准确率": metrics.get("accuracy"),
                "主要处理架构": metrics.get("primary_arch")
            }
            
            for name, value in key_metrics.items():
                if value is not None:
                    context_parts.append(f"- {name}: {value}")
        
        # === 5. 指令重述：确保LLM理解任务要求 ===
        context_parts.append("【核心任务指令】")
        context_parts.append("请基于以上上下文，重点分析以下架构特征：")
        context_parts.append("1. 预处理宏中的架构条件编译（#ifdef __arm__ 等）")
        context_parts.append("2. 内联汇编指令的架构特异性")
        context_parts.append("3. 架构相关内置函数（intrinsics）的使用")
        context_parts.append("4. 综合判断每行代码的架构依赖类别")
        
        return "\n".join(context_parts)  # 用换行符而非\n\n，更节省token

    def _extract_arch_keywords(self, code: str) -> str:
        """从代码中提取架构相关关键词，用于语义记忆检索[7](@ref)"""
        keywords = []
        arch_patterns = ["arm", "x86", "risc", "neon", "sse", "avx", "mips"]
        
        for pattern in arch_patterns:
            if pattern in code.lower():
                keywords.append(pattern)
        
        return " ".join(keywords) if keywords else "通用代码"

    
    def analyze_code(self, code: str, human_msg: str ,file_path: str = "unknown.cpp", 
                    session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        增强的代码分析方法：支持状态管理和记忆管理
        """
        # 创建或恢复会话
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_state["current_session"] = session_id
        
        try:
            # 构建上下文窗口
            context = self._build_context_window(code, file_path)
            # print("🔄 构建上下文窗口完成")
            memory_summary = self.memory_manager.summarize_memories(max_tokens=3000)
            
            

            # 执行分析流程
            
            classifications,error_lines = self.static_classifier.scan_code(code)
            print("🔄 静态规则分析推理完成")

            defined_funcs_raw, called_funcs_raw = self.function_parser.parse_functions(code, file_path)  # 调用函数解析工具
            defined_functions = self._associate_functions_with_arch(defined_funcs_raw, classifications["taggedTargets"])  # 关联架构

            # 生成报告
            report = self._generate_enhanced_report(
                human_msg,
                classifications, file_path, session_id,
                defined_functions,  
                called_funcs_raw,
                context, memory_summary     
            )

            # print("🔄 增强报告生成完成")
            # 更新状态和记忆
            self._update_after_analysis("last_analysis_result",report, file_path, session_id)
            
            # 保存状态
            self.save_agent_state()
            self.save_agent_memories()
            
            return report
            
        except Exception as e:
            # 记录错误到记忆
            error_memory = f"分析错误: {file_path} - {str(e)}"
            self.memory_manager.add_memory(
                error_memory, 
                memory_type="error",
                importance=0.8,
                metadata={"file_path": file_path, "error": str(e)}
            )
            raise e
    def analyze(self, human_msg: str ,file_path: str = "unknown.cpp", 
                    session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        增强的代码分析方法：支持状态管理和记忆管理
        """
        # 创建或恢复会话
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        
        self.current_state["current_session"] = session_id
        
        try:
            # 构建上下文窗口
            context = self._build_context_window("", file_path)
            # print("🔄 构建上下文窗口完成")
            memory_summary = self.memory_manager.summarize_memories(max_tokens=3000)            

            report = self.current_state["last_analysis_result"]
            llm_prompt = f"""
请根据以下提供的【会话历史总结】和【本次分析结果】，生成最终报告。

--- 【会话历史总结 (Agent Memory)】 ---
{memory_summary}
---

--- 【本次分析上下文及数据】 ---
分析上下文:{context}
文件路径: {file_path}
会话ID: {session_id}
分析时间: {datetime.now().isoformat()}

上次分析报告：
{report}
---

--- 【本次任务指令】 ---
用户请求原文: "{human_msg}"，请根据上次分析报告和用户的请求，尤其注意用户请求中的细节和重点，生成最终的分析报告。

请根据用户请求的复杂程度，执行以下**条件指令**：

**【模式 A：简要总结模式】**
如果用户请求内容（如“总结一下”、“有哪些架构”、“简单说一下”）表明他们只需要**快速摘要或要点**：
1.  你只需使用**自然语言文本**，简明扼要地总结主要发现。
2.  **不需要**返回 JSON 格式的详细分析结果。

**【模式 B：完整报告模式】**
如果用户请求内容（如“完整的报告”、“详细分析”、“结构化输出”）表明他们需要**完整的架构依赖报告**：
1.  首先，使用**自然语言文本**提供一个清晰、结构化的报告概览或表述。
2.  **随后**，**使用分隔符 `---JSON_DATA---` 进行严格分隔**。
3.  在分隔符之后，必须附带一个**完整的 JSON 格式数据块**，并使用 **Markdown 代码块标记 ` ```json` 和 ` ``` `** 进行封装。
    JSON 结构必须包括：
    - "architecture_summary": 架构依赖总结
    - "line_details": 每行代码的架构分类详情
    - "specific_patterns": 发现的架构特定代码模式
    - "compatibility_suggestions": 跨平台兼容性建议
    - "refactoring_suggestions": 重构建议（如需要）

请**严格**确保分隔符 `---JSON_DATA---` **只出现一次**，并位于自然语言表述和 JSON 数据块之间。
"""

            try:
                chat_prompt = ChatPromptTemplate.from_messages(
                [SystemMessage(content=self.system_prompt_template), HumanMessage(content=llm_prompt)]
                )
                chain = chat_prompt|self.llm
                # 调用LLM进行深度分析
                llm_response = chain.invoke({})
                # 解析LLM响应
                llm_analysis = self._parse_llm_response(llm_response.content)
                
            except Exception as e:
                # LLM调用失败时的降级方案
                print(f"LLM调用失败，使用基础分析结果: {str(e)}")
                
                llm_analysis = {
                    "summary": "LLM分析暂不可用，使用基础分析结果",
                    "fallback_mode": True
                }
            
            # 生成基础报告结构
            report = {
                "session_id": session_id,
                "file_path": file_path,
                "analysis_timestamp": datetime.now().isoformat(),
                "llm_enhanced_analysis": llm_analysis,
            }
            # 更新状态和记忆
            self._update_after_analysis("last_analysis_result_nocode",report, file_path, session_id)
            
            # 保存状态
            self.save_agent_state()
            self.save_agent_memories()
            
            return report
            
        except Exception as e:
            # 记录错误到记忆
            error_memory = f"分析错误: {file_path} - {str(e)}"
            self.memory_manager.add_memory(
                error_memory, 
                memory_type="error",
                importance=0.8,
                metadata={"file_path": file_path, "error": str(e)}
            )
            raise e
    
    def _associate_functions_with_arch(self, raw_funcs: List[Dict], classifications: List[Dict]) -> List[Dict]:
        """
        [辅助方法] 将原始函数定义列表与行级架构分类结果进行关联。
        """
        associated_functions = []
        # 创建一个行号到架构的快速查找字典，提高效率
        # 注意：这里的 'category' 字段名需要与你的 rule_engine 输出保持一致
        line_to_arch_map = {}
        for item in classifications:
            for line in range(item[1][0], item[1][1] + 1):
                line_to_arch_map[line]=item[2][0]
        # line_to_arch_map = {item.line_number: item.category for item in classifications}

        for func in raw_funcs:
            line_num = func['line_number']
            # 从map中查找该行对应的架构，找不到则默认为'Generic'
            arch = line_to_arch_map.get(line_num, 'Generic')
            
            associated_functions.append({
                "name": func['name'],
                "architecture": arch,
                "line_number": line_num
            })
        return associated_functions


    def _update_after_analysis(self,last_result:str,report: Dict[str, Any],
                              file_path: str, session_id: str):
        """分析后更新状态和记忆"""
        # 更新当前状态
        self.current_state[last_result] = report
        self.current_state["conversation_history"].append({
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "action": "code_analysis"
        })
        
        # 添加分析结果到记忆
        if "summary" in report:
            summary = f"分析了 {file_path}: {report['summary']['architecture_statistics']}"
            self.memory_manager.add_memory(
                summary,
                memory_type="analysis_result",
                importance=0.7,
                metadata={
                    "file_path": file_path,
                    "session_id": session_id,
                    "arch_stats": report["summary"]["architecture_statistics"]
                }
            )
            
            # 检测并记录模式
            self._detect_and_record_patterns(report, file_path)
    
    

    def _detect_and_record_patterns(self, report: Dict[str, Any], file_path: str):
        """检测并记录架构使用模式"""
        arch_stats = report["summary"]["architecture_statistics"]
        
        # 检测多架构混合模式
        if len(arch_stats) > 1:
            pattern = f"检测到多架构混合模式: {file_path} - {arch_stats}"
            self.memory_manager.add_memory(
                pattern,
                memory_type="rule_pattern",
                importance=0.9,
                metadata={"pattern_type": "multi_arch", "stats": arch_stats}
            )
        
        # 检测架构特定模式
        for arch, count in arch_stats.items():
            if count > 10:  # 阈值可调整
                pattern = f"检测到密集{arch}架构使用: {file_path} - {count}行"
                self.memory_manager.add_memory(
                    pattern,
                    memory_type="rule_pattern", 
                    importance=0.8,
                    metadata={"architecture": arch, "line_count": count}
                )
    
    def collaborate_with_specialist(self, task_type: str, task_data: Dict[str, Any], 
                                  specialist_id: str = "arch_specialist") -> Dict[str, Any]:
        """与其他专家Agent协作"""
        # 创建任务请求消息
        task_message = self.communication_bus.create_task_request(
            sender_id=self.agent_id,
            task_type=task_type,
            task_data=task_data,
            receiver_id=specialist_id
        )
        
        # 发送消息
        self.communication_bus.send_message(task_message)
        
        # 等待响应（简化实现，实际应使用异步等待）
        return {"status": "task_sent", "message_id": task_message.message_id}
    
    def handle_message(self, message: AgentMessage):
        """处理接收到的消息"""
        if message.message_type == MessageType.TASK_REQUEST:
            self._handle_task_request(message)
        elif message.message_type == MessageType.BROADCAST:
            self._handle_broadcast_message(message)
    
    def _handle_task_request(self, message: AgentMessage):
        """处理任务请求消息"""
        task_type = message.content["task_type"]
        task_data = message.content["task_data"]
        
        # 根据任务类型处理
        if task_type == "architecture_validation":
            result = self._validate_architecture(task_data)
            
            # 发送响应消息
            response_message = AgentMessage(
                message_id=str(uuid.uuid4()),
                sender_id=self.agent_id,
                receiver_id=message.sender_id,
                message_type=MessageType.TASK_RESULT,
                content={"validation_result": result},
                timestamp=datetime.now().timestamp()
            )
            self.communication_bus.send_message(response_message)
    
    def _handle_broadcast_message(self, message: AgentMessage):
        """处理广播消息"""
        # 记录重要的广播信息到记忆
        if message.content.get("importance", 0) > 0.7:
            self.memory_manager.add_memory(
                f"广播消息: {message.content}",
                memory_type="system_notification",
                importance=message.content.get("importance", 0.5)
            )
    
    def save_agent_state(self, format_type: str = "json"):
        """保存Agent状态"""
        state_to_save = {
            "current_state": self.current_state,
            "memory_count": len(self.memory_manager.memories),
            "last_saved": datetime.now().isoformat()
        }
        
        return self.state_manager.save_state(self.agent_id, state_to_save, format_type)
    
    def load_agent_state(self, version: str = "latest", format_type: str = "json"):
        """加载Agent状态"""
        state = self.state_manager.load_state(self.agent_id, format_type, version)
        if state:
            self.current_state.update(state.get("current_state", {}))
            print("load existing agent state")  # 加载已有状态
            return True
        print("initialize new agent state")  # 初始化新状态
        return False
    
    def get_agent_status(self) -> Dict[str, Any]:
        """获取Agent状态信息"""
        return {
            "agent_id": self.agent_id,
            "current_session": self.current_state["current_session"],
            "memory_count": len(self.memory_manager.memories),
            "conversation_history_count": len(self.current_state["conversation_history"]),
            "last_analysis": self.current_state["last_analysis_result"],
            "performance_metrics": self.current_state["performance_metrics"]
        }
    def _generate_enhanced_report(self, human_msg:str,classifications: Dict, file_path: str, session_id: str, 
                                  defined_functions: List[Dict], 
                                  called_functions: List[Dict],
                                  context : str, memory_summary : str) -> Dict[str, Any]:
        """
        生成增强的分析报告，整合LLM的推理能力
        """
        # 构建LLM提示词
        llm_prompt = f"""
请根据以下提供的【会话历史总结】和【本次分析结果】，生成最终报告。

--- 【会话历史总结 (Agent Memory)】 ---
{memory_summary}
---

--- 【本次分析上下文及数据】 ---
分析上下文:{context}
文件路径: {file_path}
会话ID: {session_id}
分析时间: {datetime.now().isoformat()}

分类结果概览:
{classifications}
---

--- 【本次任务指令】 ---
用户请求原文: "{human_msg}"

请根据用户请求的复杂程度，执行以下**条件指令**：

**【模式 A：简要总结模式】**
如果用户请求内容（如“总结一下”、“有哪些架构”、“简单说一下”）表明他们只需要**快速摘要或要点**：
1.  你只需使用**自然语言文本**，简明扼要地总结主要发现。
2.  **不需要**返回 JSON 格式的详细分析结果。

**【模式 B：完整报告模式】**
如果用户请求内容（如“完整的报告”、“详细分析”、“结构化输出”）表明他们需要**完整的架构依赖报告**：
1.  首先，使用**自然语言文本**提供一个清晰、结构化的报告概览或表述。
2.  **随后**，**使用分隔符 `---JSON_DATA---` 进行严格分隔**。
3.  在分隔符之后，必须附带一个**完整的 JSON 格式数据块**，并使用 **Markdown 代码块标记 ` ```json` 和 ` ``` `** 进行封装。
    JSON 结构必须包括：
    - "architecture_summary": 架构依赖总结
    - "line_details": 每行代码的架构分类详情
    - "specific_patterns": 发现的架构特定代码模式
    - "compatibility_suggestions": 跨平台兼容性建议
    - "refactoring_suggestions": 重构建议（如需要）

请**严格**确保分隔符 `---JSON_DATA---` **只出现一次**，并位于自然语言表述和 JSON 数据块之间。
"""
        
        try:
            chat_prompt = ChatPromptTemplate.from_messages(
            [SystemMessage(content=self.system_prompt_template), HumanMessage(content=llm_prompt)]
            )
            chain = chat_prompt|self.llm
            # 调用LLM进行深度分析
            llm_response = chain.invoke({})
            # 解析LLM响应
            llm_analysis = self._parse_llm_response(llm_response.content)
            
        except Exception as e:
            # LLM调用失败时的降级方案
            print(f"LLM调用失败，使用基础分析结果: {str(e)}")
            
            llm_analysis = {
                "summary": "LLM分析暂不可用，使用基础分析结果",
                "fallback_mode": True
            }
        
        # 生成基础报告结构
        report = {
            "session_id": session_id,
            "file_path": file_path,
            "analysis_timestamp": datetime.now().isoformat(),
            "llm_enhanced_analysis": llm_analysis,
            "summary": self._generate_summary_statistics(classifications["taggedTargets"]),
            "defined_functions": defined_functions, 
            "called_functions": called_functions,
            "line_details": classifications["taggedTargets"]
        }
        
        return report

    def _parse_llm_response(self, llm_output: str) -> Dict[str, Any]:
        """
        解析LLM的输出，使用分隔符 '---JSON_DATA---' 分离自然语言报告和JSON数据。
        同时，通过查找最外层的大括号，容忍JSON块前后的额外文本或分隔符。
        """
        
        DELIMITER = "---JSON_DATA---"
        json_data: Optional[Dict[str, Any]] = None
        natural_language_report: str = llm_output.strip()
        
        if DELIMITER in llm_output:
            # 1. 使用分隔符分割，获取自然语言报告和 JSON 候选区
            parts = llm_output.split(DELIMITER, 1)
            natural_language_report = parts[0].strip()
            json_candidate = parts[1].strip()

            # 2. 从 JSON 候选区中，找到最外层的 JSON 块
            # (先清理 Markdown 标记，简化查找)
            
            # 使用正则表达式清理 JSON 块周围的 Markdown 标记
            # 匹配 ```json ... ``` 或 ``` ... ``` 标记
            markdown_match = re.search(r"```json(.*?)```", json_candidate, re.DOTALL)
            if markdown_match:
                clean_json_str = markdown_match.group(1).strip()
            else:
                # 如果没有 Markdown 标记，则尝试找到最外层的 { ... }
                start_brace = json_candidate.find("{")
                end_brace = json_candidate.rfind("}")
                
                if start_brace != -1 and end_brace != -1 and start_brace < end_brace:
                    # 提取第一个 { 到最后一个 } 之间的内容，这会忽略末尾的额外分隔符
                    clean_json_str = json_candidate[start_brace : end_brace + 1].strip()
                else:
                    clean_json_str = "" # 未找到有效的JSON结构

            # 3. 尝试解析提取到的 JSON 字符串
            if clean_json_str:
                try:
                    json_data = json.loads(clean_json_str)
                    # 成功解析，json_data 已被赋值

                except json.JSONDecodeError as e:
                    # 4. JSON 解析失败，视为完整报告模式失败，全部内容归为自然语言
                    print(f"⚠️ Warning: JSON decode failed after delimiter. Error: {e}")
                    natural_language_report = llm_output.strip() # 恢复为原始输出
                    json_data = None # 确保没有返回部分失败的数据
            else:
                # 如果没有找到 {..}，也视为失败，归为自然语言
                natural_language_report = llm_output.strip()
                json_data = None
                
        # 5. 返回结果
        return {
            "natural_language_report": natural_language_report,
            "json_data": json_data,
        }
    def _generate_summary_statistics(self, classifications: List) -> Dict[str, Any]:
        """生成统计分析摘要"""
        arch_stats = {}
        for classification in classifications:
            arch = classification[2][0]  # 假设分类结果的结构为 (tagTarget, lineRange, [archs])
            arch_stats[arch] = arch_stats.get(arch, 0) + 1
        
        total_lines = len(classifications)
        arch_dependent_lines = sum(count for arch, count in arch_stats.items() 
                                if arch != "Architecture-Independent")
        
        return {
            "total_lines_analyzed": total_lines,
            "architecture_dependent_lines": arch_dependent_lines,
            "architecture_independent_lines": total_lines - arch_dependent_lines,
            "architecture_statistics": arch_stats,
            "arch_dependency_ratio": arch_dependent_lines / total_lines if total_lines > 0 else 0
        }
    def load_agent_memories(self, version: str = "latest", format_type: str = "json"):

        """加载Agent记忆"""
        return self.memory_manager.load_memories(agent_id=self.agent_id, format_type=format_type, version=version)
        
    
    def save_agent_memories(self,format_type: str = "json"):
        """保存Agent记忆"""
        return self.memory_manager.save_memories(agent_id=self.agent_id, format_type=format_type)
    
    