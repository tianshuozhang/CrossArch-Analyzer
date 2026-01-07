"""
Agent 核心模块 - 优化版：上下文管理和文件持久化
"""
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from typing import Dict, Any, List
import json
from pathlib import Path


class ArchitectureAnalysisAgent:
    """自主架构分析 Agent - 优化版"""
    
    def __init__(
        self,
        llm: ChatOpenAI,
        tools: List[Any],
        output_dir: Path,
        verbose: bool = True
    ):
        self.llm = llm
        self.tools = tools
        self.output_dir = output_dir
        self.verbose = verbose
        
        self.prompt = self._create_agent_prompt()
        self.executor = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
    
    
    def _create_agent_prompt(self) -> str:
        system_message = """# Role: 资深 C/C++ 跨平台架构专家（上下文优化版）

    你是代码架构分析专家，专注于识别硬编码的架构依赖（ARM/x86/RISC-V等）。

    ## 🔴 上下文管理红线（生死攸关）
    **你的对话上下文限制为64K tokens，超出将导致任务失败。必须严格遵守：**

    1. **数据持久化优先**: 所有分析结果必须通过 `save_analysis_result` 工具保存到文件，绝不在回复中输出原始代码或详细结果
    2. **批次处理**: 对于大项目（>50个文件），针对筛选后的文件的静态分析和手动补全必须分批分析，每批不超过50个文件，但是项目扫描和文件筛选是对所有文件一次性完成的，无需分批，因为50个文件中可能只有很少比例是架构相关的，一次性筛选可以更好地利用单次窗口长度。
    3. **碎片化读取**: 调用 `read_file` 时必须指定行号范围，单次不超过100行
    4. **定期总结**: 每处理3-5个失败文件后，在思考中总结进度，然后继续（不要把所有代码堆在上下文里）
    5. 阶段1和阶段2的结果必须一次性保存，不能重复执行。

    ## 📋 工作流（强制遵守的顺序）

    ### 阶段1: 项目扫描（必须执行）
    1. 调用 `get_project_info(info_type='summary')` 了解项目规模
    2. 调用 `get_project_info(info_type='file_list')` 获取文件列表
    3. 项目扫描只能执行一次，结果必须保存在上下文中供后续使用。

    ### 阶段2: 文件筛选（必须执行）
    1. 对所有源文件调用 `file_screening` 工具（必须使用）进行预筛选
    2. 得到可能架构相关的文件列表（通常源文件种只有很少比例是架构相关的，比如arch目录下的一般是架构相关的，以及一些misc目录下的文件或者是文件名中有架构相关关键词的）
    3. 文件筛选只进行一次，结果必须保存在上下文中供后续使用。

    ### 阶段3: 批量静态分析（核心阶段）
    1. 对file_screening筛选后的文件调用 `static_analysis`
       - 工具会自动分批处理（每批50个文件）
       - 工具会自动保存详细结果到JSON文件
       - 你只会收到统计摘要和失败文件列表
    2. **关键**: 不要尝试在回复中输出或讨论详细的代码块，这些已经保存在文件中

    ### 阶段4: 手动补全（针对失败文件）
    对于 `static_analysis` 返回的失败文件：
    1. 调用 `read_file(file_path='xxx', start_line=N-10, end_line=N+10)` 读取失败位置附近的代码
    2. 用你的专家知识分析架构依赖（识别宏、内联汇编、SIMD指令等）
    3. **立即调用 `save_analysis_result`** 保存你的分析，格式如下：
    ```json
    {
      "data_type": "manual_analysis",
      "data": {
        "path/to/file.c": {
          "status": "manual_success",
          "dominant_architecture": "ARM",
          "arch_related_blocks": [
            {
              "start_line": 105,
              "end_line": 110,
              "architecture": "ARM_NEON",
              "code_fragment": "vaddq_u8(a, b)",
              "reason": "ARM NEON intrinsic detected"
            }
          ]
        }
      }
    }
    ```
    4. 继续处理下一个失败文件，每处理3-5个后在思考中总结一次

    ### 阶段5: 生成报告（最后执行）
    在你的最终回复中：
    1. **禁止输出代码片段或详细结果**
    2. 只输出高层次的总结：
       - 项目架构类型（单一/混合/跨平台）
       - 架构分布统计（如：60% ARM, 30% x86, 10% Generic）
       - 失败文件的处理情况
       - 数据保存位置说明
    3. 告知用户详细结果已保存在哪些JSON文件中

    ## 🛠️ 工具使用规范

    ### static_analysis
    - **输入**: file_paths列表，batch_size（默认50）
    - **输出**: 统计摘要 + 失败文件列表（不包含详细代码块）
    - **注意**: 详细结果已自动保存，不会占用你的上下文

    ### read_file
    - **强制**: 必须指定 start_line 和 end_line
    - **限制**: 单次不超过100行
    - **用途**: 仅用于读取失败位置附近的代码进行手动分析

    ### save_analysis_result
    - **用途**: 保存你手动分析的结果
    - **输入**: data_type（标识）+ data（结构化数据）
    - **时机**: 每分析完一个失败文件立即保存



    ## ⚡ 专家知识要点
    识别架构依赖的关键标志：
    1. 宏定义: `__ARM_NEON`, `__AVX__`, `__riscv`, `_M_X64`
    2. 内联汇编: `__asm__`, `asm volatile`
    3. Intrinsics: `_mm_`, `vaddq_`, `__builtin_`
    4. 条件编译: `#ifdef __x86_64__`
    5. 架构特定头文件: `<arm_neon.h>`, `<emmintrin.h>`

    ## 🚨 失败预防清单
    - [ ] 项目>100个文件？使用批处理
    - [ ] 读文件时指定了行号范围？
    - [ ] 分析结果通过save_analysis_result保存了？
    - [ ] 最终回复只包含总结，没有代码片段？
    - [ ] 每处理几个文件就总结一次进度？

    请开始执行分析任务。记住：节约上下文是生存的关键！"""

        return system_message
        
    def analyze(self, user_query: str, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """执行项目分析"""
        
        input_text = f"""
**项目路径:** {project_context['project_path']}
**源文件数量:** {project_context['source_file_count']}

**用户分析需求:**
{user_query}

**重要提示:**
- 需要调用静态分析的文件: {project_context['pre_screened_files']}
- 如果超过100个文件，必须使用批处理策略
- 所有详细结果必须保存到文件，不要在回复中输出原始代码

请开始分析，严格遵守上下文管理规则。
"""
        
        print("\n" + "="*60)
        print("🤖 Agent 开始自主分析...")
        print("="*60 + "\n")
        
        try:
            result = self.executor.invoke(
                {"messages": [HumanMessage(content=input_text)]},
                config={"recursion_limit": 50} 
            )
            
            final_message = result["messages"][-1]
            all_messages = result["messages"]
            
            return {
                'status': 'success',
                'output': final_message.content,
                'intermediate_steps': all_messages,
                'final_answer': final_message.content
            }
            
        except Exception as e:
            print(f"\n❌ Agent 执行失败: {e}\n")
            return {
                'status': 'error',
                'error': str(e),
                'output': f"Agent执行过程中发生错误: {e}"
            }


class ArchitectureReportGenerator:
    """架构分析报告生成器 - 优化版：从文件读取数据"""
    
    def __init__(self, llm: ChatOpenAI, output_dir: Path):
        self.llm = llm
        self.output_dir = output_dir
    
    def load_all_analysis_results(self) -> Dict[str, Any]:
        """从保存的JSON文件中加载所有分析结果"""
        combined_results = {}
        
        # 读取静态分析批次结果
        batch_files = list(self.output_dir.glob("static_analysis_batch_*.json"))
        for batch_file in batch_files:
            try:
                with open(batch_file, 'r', encoding='utf-8') as f:
                    batch_data = json.load(f)
                    combined_results.update(batch_data)
            except Exception as e:
                print(f"⚠️  读取 {batch_file} 失败: {e}")
        
        # 读取手动补全结果
        manual_file = self.output_dir / "manual_analysis.json"
        if manual_file.exists():
            try:
                with open(manual_file, 'r', encoding='utf-8') as f:
                    manual_data = json.load(f)
                    # 合并或覆盖失败的文件
                    combined_results.update(manual_data)
            except Exception as e:
                print(f"⚠️  读取手动分析结果失败: {e}")
        
        return combined_results
    
    def extract_dependency_blocks(self) -> Dict[str, Any]:
        """从文件中提取架构依赖块信息"""
        all_results = self.load_all_analysis_results()
        dependency_map = {}
        
        for file_path, info in all_results.items():
            if info.get('status') in ['success', 'manual_success']:
                # 提取有架构依赖的文件
                blocks = info.get('arch_related_blocks', [])
                if blocks:
                    dependency_map[file_path] = {
                        'status': info['status'],
                        'dominant_architecture': info.get('dominant_architecture', 'unknown'),
                        'arch_related_blocks': blocks
                    }
        
        return dependency_map
    
    def generate_structured_report(
        self,
        agent_output: str,
        intermediate_steps: List[Any],
        user_query: str
    ) -> Dict[str, Any]:
        """生成结构化报告"""
        
        tool_calls_summary = self._summarize_tool_calls(intermediate_steps)
        raw_dependencies = self.extract_dependency_blocks()
        
        # 统计信息
        total_files = len(raw_dependencies)
        arch_distribution = {}
        for file_info in raw_dependencies.values():
            arch = file_info['dominant_architecture']
            arch_distribution[arch] = arch_distribution.get(arch, 0) + 1
        
        # 使用LLM生成最终报告
        from langchain_core.messages import SystemMessage, HumanMessage
        
        system_prompt = """你是技术报告编写专家。根据架构分析结果生成清晰的报告。

报告结构：
1. **执行摘要** - 项目架构类型和关键发现
2. **架构分布** - 各架构的文件数量和占比
3. **风险评估** - 移植性风险等级（低/中/高）
4. **优化建议** - 具体改进方案

用Markdown格式输出，简洁专业。"""

        human_prompt = f"""
**用户需求:** {user_query}

**分析统计:**
- 分析文件总数: {total_files}
- 架构分布: {json.dumps(arch_distribution, ensure_ascii=False)}

**Agent执行摘要:**
{agent_output[:500]}...

**工具使用记录:**
{tool_calls_summary}

请生成结构化报告（不要包含原始代码片段）。"""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ])
            
            return {
                'structured_report': response.content,
                'agent_output': agent_output,
                'raw_dependency_data': raw_dependencies,
                'statistics': {
                    'total_analyzed_files': total_files,
                    'architecture_distribution': arch_distribution
                },
                'tool_calls_summary': tool_calls_summary,
                'data_location': str(self.output_dir)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'agent_output': agent_output,
                'raw_dependency_data': raw_dependencies,
                'tool_calls_summary': tool_calls_summary
            }
    
    def _summarize_tool_calls(self, messages: List[Any]) -> str:
        """总结工具调用记录（简化版）"""
        if not messages:
            return "Agent 未调用任何工具"
        
        summary_lines = ["Agent 工具调用记录:"]
        counter = 1
        
        for i, msg in enumerate(messages):
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call['name']
                    summary_lines.append(f"{counter}. {tool_name}")
                    counter += 1
                    
                    # 只保留关键工具的部分参数
                    if tool_name == 'static_analysis':
                        args = tool_call.get('args', {})
                        file_count = len(args.get('file_paths', []))
                        summary_lines.append(f"   - 分析文件数: {file_count}")
        
        return "\n".join(summary_lines)