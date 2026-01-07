"""
项目架构分析编排器 - 优化版：上下文管理和持久化存储
"""
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))# 获取当前文件所在目录
LLM_dir = os.path.dirname(current_dir)# 获取LLM目录
sys.path.append(LLM_dir)# 将LLM目录添加到sys.path中
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List
import json
from datetime import datetime
import time
from pathlib import Path

from agents.file_utils import FileScanner
from agents.static_tool_wrapper import StaticAnalysisWrapper
from agents.agent_tools import (
    FileScreeningTool,
    StaticAnalysisTool,
    FileReaderTool,
    ProjectInfoTool,
    SaveAnalysisResultTool
)
from agents.agent_core import ArchitectureAnalysisAgent, ArchitectureReportGenerator

from core.state_manager import StateManager
from core.memory_manager import MemoryManager
from langchain_classic.memory import ConversationBufferWindowMemory
from utils import setup_environment


class ProjectArchitectureOrchestrator:
    """项目架构分析编排器 - 优化版"""
    
    def __init__(self, llm_config: Dict[str, Any], agent_id: str = "arch_agent_001"):
        self.agent_id = agent_id
        self.llm = ChatOpenAI(**llm_config)
        
        # 状态和记忆管理
        self.state_manager = StateManager()
        self.long_term_knowledge = MemoryManager(model_name="./LLM/models/all-MiniLM-L6-v2")
        self.session_memory = ConversationBufferWindowMemory(
            k=20,  # 减少到20以节省上下文
            memory_key="chat_history",
            return_messages=True
        )
        
        # 工具组件
        self.file_scanner = None
        self.static_analyzer = StaticAnalysisWrapper()
        
        # Agent组件
        self.agent = None
        self.report_generator = None
        
        print(f"✅ 优化版Agent编排器 {self.agent_id} 初始化完成")
    
    def analyze_project(self, project_path: str, user_query: str) -> Dict[str, Any]:
        """分析项目的完整流程"""
        print(f"\n{'='*60}")
        print(f"🚀 开始项目架构依赖分析（优化版）")
        print(f"📁 项目路径: {project_path}")
        print(f"💬 用户需求: {user_query}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        # 1. 创建输出目录（用于保存JSON结果）
        output_dir = Path(project_path) / ".arch_analysis_results"
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📂 结果保存目录: {output_dir}\n")
        
        # 2. 初始化文件扫描器
        try:
            self.file_scanner = FileScanner(project_path)
        except Exception as e:
            return self._create_error_response(f"文件扫描器初始化失败: {e}")
        
        # 3. 快速扫描项目结构
        all_files = self.file_scanner.scan_all_files()
        file_tree = ""  # 不生成完整文件树以节省内存
        file_tree = self.file_scanner.build_file_tree(max_depth=10) 

        file_count = len(all_files['source_files'])
        print(f"📊 项目结构扫描完成:")
        print(f"  - 源文件: {file_count} 个")
        print(f"  - 构建文件: {len(all_files['build_files'])} 个")

        # 4. 自动化预筛选（静默执行）
        print(f"🔍 正在对 {file_count} 个文件进行启发式预筛选...")
        from agents.file_utils import ArchitectureHeuristics

        pre_screened_files = []
        for file_path in all_files['source_files']:
            # 使用你已有的启发式规则
            is_arch, _ = ArchitectureHeuristics.is_likely_arch_related(file_path, None)
            if is_arch:
                pre_screened_files.append(file_path)

        print(f"✅ 预筛选完成：识别出 {len(pre_screened_files)} 个潜在架构相关文件")

        # 将筛选后的结果直接放入 project_context
        project_context = {
            'project_path': project_path,
            'source_file_count': file_count,
            'pre_screened_files': pre_screened_files, # 关键：给 Agent 的是精简版
            'build_files': all_files['build_files'],
        }
        # # 4. 根据文件数量调整策略
        # if file_count > 200:
        #     print(f"⚠️  大型项目检测（{file_count}个文件），将使用严格的批处理策略\n")
        
        # project_context = {
        #     'project_path': project_path,
        #     'source_file_count': file_count,
        #     'build_files': all_files['build_files'],
        #     'doc_files': all_files['doc_files']
        # }
        
        # 5. 创建Agent及其工具（传入output_dir）
        tools = self._create_agent_tools(all_files, file_tree, output_dir)
        self.agent = ArchitectureAnalysisAgent(
            llm=self.llm,
            tools=tools,
            output_dir=output_dir,
            verbose=True
        )
        self.report_generator = ArchitectureReportGenerator(self.llm, output_dir)
        
        print("🔧 Agent 工具初始化完成\n")
        
        # 6. 让Agent自主执行分析
        agent_result = self.agent.analyze(user_query, project_context)
        
        if agent_result['status'] != 'success':
            return self._create_error_response(
                f"Agent 分析失败: {agent_result.get('error', 'Unknown error')}"
            )
        
        print("\n" + "="*60)
        print("✅ Agent 分析完成")
        print("="*60 + "\n")
        
        # 7. 生成结构化报告
        print("📝 正在生成结构化报告...\n")
        
        structured_report = self.report_generator.generate_structured_report(
            agent_output=agent_result['output'],
            intermediate_steps=agent_result.get('intermediate_steps', []),
            user_query=user_query
        )
        
        # 8. 组装最终输出
        end_time = time.time()
        execution_time = end_time - start_time
        
        final_report = {
            'project_path': project_path,
            'user_query': user_query,
            'project_statistics': {
                'total_source_files': file_count,
                'analyzed_files': structured_report.get('statistics', {}).get('total_analyzed_files', 0),
                'architecture_distribution': structured_report.get('statistics', {}).get('architecture_distribution', {})
            },
            'agent_summary': agent_result['output'],
            'structured_report': structured_report.get('structured_report', ''),
            'data_location': str(output_dir),
            'raw_data_available': True,
            'execution_time': execution_time,
            'generated_at': datetime.now().isoformat()
        }
        
        # 9. 保存最终报告到文件
        report_file = output_dir / "final_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        
        print(f"{'='*60}")
        print(f"✅ 项目分析完成")
        print(f"⏱️  总耗时: {execution_time:.2f} 秒")
        print(f"📊 分析文件: {structured_report.get('statistics', {}).get('total_analyzed_files', 0)}/{file_count}")
        print(f"💾 详细数据保存在: {output_dir}")
        print(f"{'='*60}\n")
        
        # 保存到记忆（可选）
        self._save_to_memory(project_path, user_query, final_report)
        
        return final_report
    
    def _create_agent_tools(
        self,
        all_files: Dict[str, List[str]],
        file_tree: str,
        output_dir: Path
    ) -> List[Any]:
        """创建Agent可用的工具列表"""
        tools = [
            # ProjectInfoTool(
            #     file_scanner=self.file_scanner,
            #     all_files=all_files,
            #     file_tree=file_tree
            # ),
            
            FileReaderTool(
                file_scanner=self.file_scanner,
                max_lines_per_read=100  # 强制限制
            ),
            
            # FileScreeningTool(
            #     file_scanner=self.file_scanner
            # ),
            
            StaticAnalysisTool(
                file_scanner=self.file_scanner,
                static_analyzer=self.static_analyzer,
                output_dir=output_dir
            ),
            
            # 新增：保存分析结果工具
            SaveAnalysisResultTool(
                output_dir=output_dir
            )
        ]
        
        return tools
    
    def get_raw_analysis_data(self, project_path: str) -> Dict[str, Any]:
        """获取原始分析数据（从保存的文件中读取）"""
        output_dir = Path(project_path) / ".arch_analysis_results"
        
        if not output_dir.exists():
            return {'error': '未找到分析结果目录'}
        
        # 读取最终报告
        report_file = output_dir / "final_report.json"
        if report_file.exists():
            with open(report_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {'error': '未找到分析报告'}
    
    def get_dependency_blocks(self, project_path: str) -> Dict[str, Any]:
        """获取架构依赖块的详细数据"""
        output_dir = Path(project_path) / ".arch_analysis_results"
        
        if not self.report_generator:
            self.report_generator = ArchitectureReportGenerator(self.llm, output_dir)
        else:
            self.report_generator.output_dir = output_dir
        
        return self.report_generator.extract_dependency_blocks()
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            'status': 'error',
            'error': error_message,
            'generated_at': datetime.now().isoformat()
        }
    
    def _save_to_memory(
        self,
        project_path: str,
        user_query: str,
        result: Dict[str, Any]
    ):
        """保存分析结果到记忆系统"""
        try:
            memory_entry = {
                'project': project_path,
                'query': user_query,
                'summary': result.get('agent_summary', '')[:300],
                'timestamp': result['generated_at']
            }
            
            self.session_memory.save_context(
                {"input": user_query},
                {"output": result.get('agent_summary', '')[:200]}
            )
            
            print("💾 分析结果已保存到记忆系统")
            
        except Exception as e:
            print(f"⚠️  保存到记忆失败: {e}")
    
    def query_history(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """查询历史分析记录"""
        try:
            results = self.long_term_knowledge.retrieve_messages(query, top_k=top_k)
            return [json.loads(r['content']) for r in results]
        except Exception as e:
            print(f"⚠️  查询历史失败: {e}")
            return []


# ============================================================================
# 使用示例
# ============================================================================

def example_usage():
    """示例：如何使用优化版编排器"""
    
    setup_environment()
    from agents.ProjectArchitectureOrchestrator import ProjectArchitectureOrchestrator
    llm_config = {
        "model": "deepseek-v3:671b",  # 模型名称
        "openai_api_key": os.environ["OPENAI_API_KEY"],
        "openai_api_base": os.environ["OPENAI_API_BASE"],
        "temperature": 0.2
    }
    orchestrator = ProjectArchitectureOrchestrator(llm_config)
        
    # 分析项目
    # result = orchestrator.analyze_project(
    #     project_path="LLM/config/test_project",
    #     user_query="请分析这个项目的架构依赖情况，特别关注 ARM 和 x86 架构的兼容性"
    # )
    result = orchestrator.analyze_project(
        project_path="LLM/config/eigen",
        user_query="请分析这个项目的架构依赖情况，特别关注 ARM 和 x86 架构的兼容性"
    )
        
    # 打印报告
    print("\n" + "="*60)
    print("📄 结构化报告:")
    print("="*60)
    print(result['structured_report'])
    
    print("\n" + "="*60)
    print("📊 统计信息:")
    print(json.dumps(result['project_statistics'], indent=2, ensure_ascii=False))
    
    print("\n" + "="*60)
    print(f"💾 详细数据位置: {result['data_location']}")
    print("="*60)
    
    # 获取原始依赖块数据
    dependency_blocks = orchestrator.get_dependency_blocks("LLM/config/eigen")
    print(f"\n找到 {len(dependency_blocks)} 个架构依赖文件")
    
    # 保存依赖块数据供后续使用
    with open("dependency_blocks.json", "w", encoding="utf-8") as f:
        json.dump(dependency_blocks, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    example_usage()