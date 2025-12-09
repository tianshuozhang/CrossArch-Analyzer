from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage,BaseMessage
from typing import Dict, Any, List, Optional,Tuple
import json
from datetime import datetime

from langchain_classic.memory import ConversationBufferWindowMemory
from core.state_manager import StateManager
from core.memory_manager import MemoryManager
# 引入 LCEL 核心组件
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from pydantic.v1 import BaseModel,Field
# ... 确保导入了所有必要的 LangChain 模块 ...
from agents.enhanced_orchestrator import EnhancedOrchestratorAgent

class ProjectTask(BaseModel):
    task_type: str = Field(description="项目任务类型，可选值: 'build_audit', 'risk_correlation', 'project_report'")
    instruction: str = Field(description="任务的详细说明和目标，例如 '调查构建标志与代码宏的冲突'。")
    input_data: str = Field(description="任务执行所需的关键输入数据（摘要或片段）。")

class ProjectPlanning(BaseModel):
    project_plan: List[ProjectTask] = Field(description="项目级架构分析的有序执行计划。")

class Project_orchestrator(EnhancedOrchestratorAgent):
    """增强的主控智能体：支持状态管理、记忆管理和多Agent协作"""
    
    def __init__(self, llm_config: Dict[str, Any], agent_id: str = "pro_orchestrator_001"):
        self.agent_id = agent_id
        
        self.llm = ChatOpenAI(**llm_config)
        
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
        
    def _summarize_project_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        将完整的项目报告提炼为 LLM 易于处理的摘要。
        """
        single_file_summaries = []
        # 逐文件提取架构统计信息
        for filename,file_result in report.get("single_file_analysis", []).items():
            analysis_data = file_result.get("summary", {})
            arch_stats = analysis_data.get("architecture_statistics", {})
            
            # 只提取非无关架构的统计
            arch_usage = {k: v for k, v in arch_stats.items() if k != "irrelevant"}
            
            single_file_summaries.append({
                "file_path": filename,
                "arch_usage": arch_usage,
                "dependency_ratio": analysis_data.get("arch_dependency_ratio", 0)
            })

        return {
            "build_context_summary": report.get("build_context", {}),
            "project_level_issues": report.get("project_level_issues", []),
            "file_architecture_summaries": single_file_summaries
        }

    def _create_project_planning_chain(self) -> Tuple[RunnablePassthrough, JsonOutputParser]:
        """创建项目级任务分解的 LCEL 链。"""
        
        json_parser = JsonOutputParser(pydantic_object=ProjectPlanning)

        system_prompt = f"""
        你是一个专业的项目架构审计和编排智能体。你的任务是基于项目的构建上下文、跨文件问题和逐文件分析摘要，制定一个清晰的项目级架构判断计划。

        **执行规则:**
        1. 计划必须严格遵循提供的 JSON Schema (ProjectPlanning) 进行输出。
        2. 必须覆盖构建配置与代码依赖的审计、跨文件风险的关联分析。
        3. 最终必须包含一个 'project_report' 步骤。
        
        **任务类型说明:**
        - **build_audit:** 审计构建系统配置与实际代码依赖的一致性。
        - **risk_correlation:** 关联分析跨文件问题 (project_level_issues) 与总体架构风险。
        - **project_report:** 最终的架构判断、风险总结和建议。
        """
        
        human_prompt_template = """
        请基于以下项目的关键摘要信息，制定详细的项目级架构分析执行计划：

        1. **构建配置摘要 (Build Context):** {build_context}
        2. **跨文件关联问题 (Project Issues):** {project_issues}
        3. **逐文件架构依赖摘要 (File Summaries):** {file_summaries}

        请输出遵循以下 JSON 格式的计划：
        {format_instructions}
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt_template)
        ])

        planning_chain = (
            prompt 
            | self.llm.bind(stop=["\nObservation"])
            | json_parser
        )
        
        return planning_chain, json_parser

    def _build_project_investigation_prompt(self, instruction: str, input_data: str) -> List[BaseMessage]:
        """构建用于项目级审计和风险关联的 Prompt"""
        
        system_prompt = f"""
        你是一个专业的项目架构和依赖分析师。你的任务是根据指令和项目数据，进行深度审计或风险关联分析，并给出技术结论。
        
        **输出要求:** 简洁、技术性强，直接回答指令中提出的问题，例如：'为什么构建系统可能与代码使用不一致' 或 '跨文件缺失的实现可能造成何种架构风险'。
        """
        
        human_prompt = f"""
        **分析指令:** {instruction}
        
        **输入数据片段 (作为分析依据):**
        ---
        {input_data}
        ---

        请提供你的技术分析和结论。
        """
        return [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]

    def analyze_project_architecture(self, full_project_report: Dict[str, Any], user_msg: str) -> Dict[str, Any]:
        """
        对完整的项目报告进行架构判断和任务编排。
        """
        print("▶️ 开始项目级架构分析和任务编排...")
        
        # 1. 提炼项目报告摘要
        project_summary = self._summarize_project_report(full_project_report)
        
        # 2. 创建并调用项目规划链
        planning_chain, json_parser = self._create_project_planning_chain()
        
        planner_input = {
            "build_context": json.dumps(project_summary["build_context_summary"], indent=2),
            "project_issues": json.dumps(project_summary["project_level_issues"], indent=2),
            "file_summaries": json.dumps(project_summary["file_architecture_summaries"], indent=2),
            "format_instructions": json_parser.get_format_instructions()
        }
        
        task_planning_result: Dict[str, Any] = planning_chain.invoke(planner_input)
        task_plan: List[Dict] = task_planning_result.get('project_plan', [])
        
        if not task_plan:
            raise Exception("LLM未能生成有效的项目分析计划。")

        print(f"✅ 成功解析到 {len(task_plan)} 个项目级任务。")
        
        # 3. 迭代执行项目级任务
        analysis_results = []
        final_project_report = None
        
        for task in task_plan:
            task_type = task['task_type']
            instruction = task['instruction']
            task_input = task['input_data'] # 使用 input_data 键

            if task_type in ["build_audit", "risk_correlation"]:
                print(f"🔎 执行 {task_type} 任务: {instruction}")
                # LLM 调用 2: 专门进行审计或关联分析
                investigation_prompt = self._build_project_investigation_prompt(instruction, task_input)
                llm_response = self.llm.invoke(investigation_prompt)
                
                analysis_results.append({
                    "task_type": task_type,
                    "instruction": instruction,
                    "analysis": llm_response.content
                })
            
            elif task_type == "project_report":
                print("📝 执行项目级报告生成任务...")
                
                # LLM 调用 3: 生成最终报告
                final_project_report = self._generate_final_project_report(
                    full_project_report, 
                    user_msg, 
                    analysis_results
                )
                break
            
        return final_project_report


    def _generate_final_project_report(self, full_report: Dict[str, Any], user_msg: str, analysis_results: List[Dict]) -> Dict[str, Any]:
        """
        生成最终的项目级架构判断和总结报告。
        """
        
        # 整合所有分析结果
        analysis_context = "\n\n".join([
            f"--- {res['task_type']} 结果 ---\n指令: {res['instruction']}\n结论: {res['analysis']}" 
            for res in analysis_results
        ])
        
        system_prompt = f"""
        你是一个顶级的项目架构师。你的任务是综合所有的分析结果和原始数据，为用户生成一份完整的项目级架构判断报告。
        
        **报告必须包含:**
        1. **项目架构类型判断:** (例如：'单一架构-ARM'，'混合架构-ARM/RISC-V'，'可移植性高')
        2. **核心架构风险评估:** (基于 build_audit 和 risk_correlation 结果)
        3. **具体优化建议:** 如何提高跨平台兼容性或消除架构依赖风险。
        """

        human_prompt = f"""
        **用户初始请求/关注点:** {user_msg}
        
        **原始项目级问题摘要 (Project Issues):** {json.dumps(full_report['project_level_issues'], indent=2)}
        
        **LLM 分析与审计结果:**
        ---
        {analysis_context}
        ---

        请基于以上所有信息，生成最终的、专业的、结构化的项目级架构判断报告。
        """
        
        llm_response = self.llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)])
        
        # 返回结果结构，便于后续前端展示或进一步处理
        return {
            "project_details": full_report,
            "user_request": user_msg,
            "final_architecture_judgment": llm_response.content,
            "detailed_analysis_steps": analysis_results
        }