from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage,BaseMessage
from typing import Dict, Any, List, Optional,Tuple
import json
from datetime import datetime
import re
from core.function_parser_tool import FunctionParserTool

from langchain_classic.memory import ConversationBufferWindowMemory
from core.state_manager import StateManager
from core.memory_manager import MemoryManager
import uuid
from core.Static_CodeAnalyzer import Static_CodeAnalyzer
# 引入 LCEL 核心组件
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from pydantic.v1 import BaseModel,Field

class Task(BaseModel):
    task_type: str = Field(description="任务类型，可选值: 'analysis', 'investigation', 'report'")
    instruction: str = Field(description="任务的详细说明和目标。")
    input: str = Field(description="执行该任务所需的输入数据或上下文。")

# 定义最终的规划输出结构
class Planning(BaseModel):
    plan: List[Task] = Field(description="任务执行计划的有序列表。")

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
        # 1. 长期/事实记忆 (保留您的自定义 MemoryManager)
        # 负责存储分析结果、架构模式等结构化数据，用于语义检索。
        self.long_term_knowledge = MemoryManager(model_name="./LLM/models/all-MiniLM-L6-v2") 
        
        # 2. 短期/会话记忆 (使用 LangChain ConversationBufferWindowMemory)
        # 负责存储和总结用户与 Orchestrator 之间的对话历史。
        self.session_memory = ConversationBufferWindowMemory(
            k=50,  # 存储最近50条消息
            memory_key="chat_history", # 约定键名
            return_messages=True     # 返回消息对象列表，便于构建 Prompt
        )
        
        # 当前状态
        self.current_state = {
            "agent_id": self.agent_id,
            "current_session": self.session_memory,
            "last_analyzed_code": None,
            "last_analysis_result": None,
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
        1.  首先，使用**自然语言文本**提供一个清晰、结构化的报告概览或表述,对于跨平台兼容性和整体代码的架构依赖性要进行详细思考后给出回答。
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
        
        
    
    def _build_context_window(self, code: str, file_path: str) -> str:
        """构建上下文窗口：将相关状态和记忆加载到LLM上下文[4](@ref)[8](@ref)"""
        
        context_parts = []
        
        # === 1. 关键信息前置：当前任务摘要（最高优先级）[6](@ref)[8](@ref) ===
        context_parts.append("【当前分析任务】")
        context_parts.append(f"文件路径: {file_path}")
        context_parts.append(f"代码规模: {len(code.splitlines())} 行代码")
        context_parts.append(f"分析目标: 识别代码中对特定指令集架构(如ARM, x86, RISC-V)的依赖")
        context_parts.append("###")  # 清晰的分隔符[7](@ref)

        # === 2. 短期/会话历史 (来自 LangChain Memory) ===
        # LangChain 会自动决定是返回完整历史还是总结
        history_vars = self.session_memory.load_memory_variables({})
        chat_history_messages: List[BaseMessage] = history_vars.get("chat_history", [])
        
        if chat_history_messages:
            # 将 LangChain 的 Message 对象列表格式化为 Prompt 字符串
            formatted_history = "\n".join([f"[{msg.type.capitalize()}]: {msg.content}" for msg in chat_history_messages])
            
            context_parts.append("【会话历史摘要】")
            context_parts.append(formatted_history)
            context_parts.append("###")
        
        # === 3. 动态记忆检索：基于当前代码内容的语义搜索[7](@ref) ===
        query_keywords = self._extract_arch_keywords(code)  # 从代码中提取架构相关关键词
        semantic_query = f"代码分析 {query_keywords} {file_path}"
        
        relevant_memories = self.long_term_knowledge.retrieve_relevant_memories(
            semantic_query,  # 使用语义更丰富的查询
            memory_type="analysis_result",
            top_k=3  # 限制数量，保证相关性[5](@ref)
        )
        
        if relevant_memories:
            context_parts.append("【相关历史分析】")
            for i, memory in enumerate(relevant_memories[:3]):  # 最多2条最相关记忆
                context_parts.append(f"{i+1}. {memory.content}")
            context_parts.append("###")
        
        # === 4. 会话状态：上次分析结果（如果存在）===
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
        if code == "":
            code =  self.current_state["last_analyzed_code"] 
        else :
            self.current_state["last_analyzed_code"] = code
        try:
            # 1. 静态规则分析阶段
            classifications,error_lines = self.static_classifier.scan_code(code)
            print("🔄 静态规则分析推理完成")

            defined_funcs_raw, called_funcs_raw = self.function_parser.parse_functions(code, file_path)  # 调用函数解析工具
            defined_functions = self._associate_functions_with_arch(defined_funcs_raw, classifications["taggedTargets"])  # 关联架构

            # 2.   构建上下文窗口
            context = self._build_context_window(code, file_path)
            # print("🔄 构建上下文窗口完成")
            memory_summary = self.long_term_knowledge.summarize_memories(max_tokens=3000)
            
            # 3. 任务编排/规划阶段 (LCEL 链调用)
            planning_chain,json_parser = self._create_planning_chain()
            
            # 准备 LCEL 链的输入字典
            planner_input = {
                "user_prompt": human_msg,
                "arch_analysis": classifications,
                "error_line_count": 0 if error_lines is None else len(error_lines),
                "error_info": self._generate_error_info(error_lines),
                "context": context,
                "format_instructions": json_parser.get_format_instructions() # 获取 Pydantic 格式指令
            }

            print("▶️ 调用 LangChain 规划链制定任务执行计划...")
        
            # 核心 LCEL 调用
            task_planning_result: Dict[str, Any] = planning_chain.invoke(planner_input) 

            # 关键修正：从字典中提取 'plan' 列表
            task_plan = task_planning_result['plan'] # 使用 ['plan'] 键访问，而不是 .plan

            print(f"✅ 规划链成功解析到 {len(task_plan)} 个任务。")
            

            # 4. 迭代执行任务 (逻辑与您之前的实现保持一致)
            investigation_results = []
            # ... [任务执行循环保持不变，使用 task_plan] ...
            for task in task_plan:
                task_type = task['task_type'] 
                instruction = task['instruction']
                task_input = task['input']
                
                if task_type == "investigation":
                    # ... [调用 _build_investigation_prompt 和 self.llm.invoke 的逻辑] ...
                    print(f"🔎 执行调查任务: {instruction}")
                    investigation_prompt = self._build_investigation_prompt(
                        code, instruction, task_input, file_path
                    )
                    investigation_response = self.llm.invoke(investigation_prompt)
                    investigation_results.append({
                        "instruction": instruction,
                        "result": investigation_response.content
                    })

                elif task_type == "report":
                    # ... [调用 _generate_enhanced_report 的逻辑] ...
                    print("📝 执行报告生成任务...")
                    report = self._generate_enhanced_report(
                        human_msg,
                        classifications, file_path, session_id,
                        defined_functions, 
                        called_funcs_raw,
                        context, memory_summary,
                        investigation_results 
                    )
                    final_report = report
                    break  # 报告任务完成后退出循环
                
                elif task_type == "analysis":
                    print(f"✔️ 静态分析任务已完成: {instruction}")

            # 5. 记忆和状态保存 (保持不变)
            if final_report:
                self.current_state["last_analysis_result"] = final_report
                llm_report_text = final_report["llm_enhanced_analysis"]["natural_language_report"]
                self.session_memory.save_context({"input": human_msg}, {"output": llm_report_text})
                self._update_after_analysis("last_analysis_result", final_report, file_path, session_id)
                self.save_agent_state()
                self.save_agent_memories()
                return final_report
            else:
                raise Exception("任务编排流程未能生成最终报告。")
                
        except Exception as e:
            # ... [错误记录逻辑保持不变] ...
            error_memory = f"分析错误: {file_path} - {str(e)}"
            self.long_term_knowledge.add_memory(
                error_memory, 
                memory_type="error",
                importance=0.8,
                metadata={"file_path": file_path, "error": str(e)}
            )
            raise e
    def analyze(self, human_msg: str ,file_path: str = "unknown.cpp", 
                    session_id: Optional[str] = None) -> Dict[str, Any]:
        """简化版分析接口：仅基于提示词进行分析"""
        return self.analyze_code("", human_msg, file_path, session_id)
    
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
        
        
        # 添加分析结果到到长期记忆库
        if "summary" in report:
            summary = f"分析了 {file_path}: {report['summary']['architecture_statistics']}"
            self.long_term_knowledge.add_memory(
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
            self.long_term_knowledge.add_memory(
                pattern,
                memory_type="rule_pattern",
                importance=0.9,
                metadata={"pattern_type": "multi_arch", "stats": arch_stats}
            )
        
        # 检测架构特定模式
        for arch, count in arch_stats.items():
            if count > 10:  # 阈值可调整
                pattern = f"检测到密集{arch}架构使用: {file_path} - {count}行"
                self.long_term_knowledge.add_memory(
                    pattern,
                    memory_type="rule_pattern", 
                    importance=0.8,
                    metadata={"architecture": arch, "line_count": count}
                )

    
    
    def save_agent_state(self, format_type: str = "json"):
        """保存Agent状态"""
        state_to_save = {
            "current_state": self.current_state,
            "memory_count": len(self.long_term_knowledge.memories),
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
            "memory_count": len(self.long_term_knowledge.memories),
            "last_analysis": self.current_state["last_analysis_result"],
            "performance_metrics": self.current_state["performance_metrics"]
        }
    def _generate_enhanced_report(self, human_msg:str,classifications: Dict, file_path: str, session_id: str, 
                                  defined_functions: List[Dict], 
                                  called_functions: List[Dict],
                                  context : str, memory_summary : str,investigation_results :List[Dict]) -> Dict[str, Any]:
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

静态分析分类结果概览:
{classifications}

此前调查结果概览:
{investigation_results}
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
1.  首先，使用**自然语言文本**提供一个清晰、结构化的报告概览或表述,对于跨平台兼容性和整体代码的架构依赖性要进行详细思考后给出回答。
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
        return self.long_term_knowledge.load_memories(agent_id=self.agent_id, format_type=format_type, version=version)
        
    
    def save_agent_memories(self,format_type: str = "json"):
        """保存Agent记忆"""
        return self.long_term_knowledge.save_memories(agent_id=self.agent_id, format_type=format_type)
    
    def _create_planning_chain(self) -> RunnablePassthrough:
        """
        创建用于任务分解和编排的 LCEL 链。
        """
        # 1. 定义输出解析器
        json_parser = JsonOutputParser(pydantic_object=Planning)

        # 2. 定义系统提示词 (用于规划和JSON格式要求)
        system_prompt = f"""
        你是一个专业的任务编排智能体（Orchestrator）。你的任务是根据用户的需求和当前代码的静态分析结果，制定一个清晰的分步执行计划。
        
        **执行规则:**
        1. 必须优先解决用户需求和静态分析中的 'Error Lines'。
        2. 你的计划必须严格遵循提供的 JSON Schema 进行输出。
        3. 必须包含至少一个 'report' 步骤作为收尾。
        
        **任务类型说明:**
        - **analysis:** 对代码进行详细分析和架构标记（通常视为已完成）。
        - **investigation:** 针对静态分析无法解决的错误行或模糊点，调用额外的 LLM 知识进行推理。
        - **report:** 最终的报告生成步骤，将所有信息整合为最终报告。
        """
        
        # 3. 定义人类提示词模板
        human_prompt_template = """
        请根据以下信息制定任务执行计划：

        1. **用户需求:** {user_prompt}
        2. **详细的静态分析:** {arch_analysis}
        3. **静态分析未解决的错误行 (Error Lines):**
           总计 {error_line_count} 行。具体信息: {error_info}
        4. **已知上下文/历史:** {context}

        请输出遵循以下 JSON 格式的计划：
        {format_instructions}
        """

        # 4. 构建 ChatPromptTemplate
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt_template)
        ])

        # 5. 构建 LCEL 链: prompt | llm | parser
        planning_chain = (
            prompt 
            | self.llm.bind(stop=["\nObservation"]) # 绑定 LLM
            | json_parser # 解析 JSON 输出
        )
        
        return planning_chain,json_parser
    def _generate_error_info(self, error_lines: List[Tuple[int, str]]) -> str:
        """（辅助方法）将错误行格式化为字符串"""
        if not error_lines:
            return "无错误行。"
        return "\n".join([f"行 {line}: '{snippet}'" for line, snippet in error_lines])
    def _build_investigation_prompt(self, code: str, instruction: str, input_data: str, file_path: str) -> List[BaseMessage]:
        """构建用于调查/推理特定代码或错误行的 Prompt"""
        
        system_prompt = f"""
        你是一个专业的代码推理和调试智能体。你的任务是根据给定的指令和代码上下文，深入调查静态分析无法处理的错误行或模糊点。
        
        **目标:** 严格遵循指令，对给定的代码片段或错误信息进行推理，找出导致静态分析失败的可能原因，并给出技术判断。
        """
        
        human_prompt = f"""
        **文件路径:** {file_path}
        **当前指令:** {instruction}
        
        **代码上下文:**
        ---
        {code}
        ---
        
        **需要调查的输入/错误信息:**
        ---
        {input_data}
        ---

        请根据代码上下文和输入信息，提供你的技术分析和结论。
        """
        
        return [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]