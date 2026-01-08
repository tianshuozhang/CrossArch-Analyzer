"""
项目架构分析编排器 - 单文件循环模式优化版
核心改进：外部控制循环，消除Agent任务畏惧
"""
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
LLM_dir = os.path.dirname(current_dir)
sys.path.append(LLM_dir)

from langchain_openai import ChatOpenAI
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import time
from pathlib import Path
from enum import Enum

from agents.file_utils import FileScanner
from agents.static_tool_wrapper import StaticAnalysisWrapper
from agents.agent_tools import (
    FileReaderTool,
    StaticAnalysisTool,
    SaveAnalysisResultTool
)
from agents.agent_core import (
    ArchitectureAnalysisAgent, 
    ArchitectureReportGenerator,
    SingleFileAnalysisAgent  # 新增：专门处理单文件的Agent
)

from core.state_manager import StateManager
from core.memory_manager import MemoryManager
from langchain_classic.memory import ConversationBufferWindowMemory
from utils import setup_environment



class AnalysisPhase(Enum):
    """分析阶段枚举"""
    INIT = "init"
    PRE_SCREENING = "pre_screening"
    STATIC_ANALYSIS = "static_analysis"
    MANUAL_PROCESSING = "manual_processing"
    REPORT_GENERATION = "report_generation"
    COMPLETED = "completed"
    ERROR = "error"


class ProjectArchitectureOrchestrator:
    """项目架构分析编排器 - 状态机驱动版"""
    
    def __init__(self, llm_config: Dict[str, Any], agent_id: str = "arch_agent_001"):
        self.agent_id = agent_id
        self.llm = ChatOpenAI(**llm_config)
        
        # 状态管理
        self.current_phase = AnalysisPhase.INIT
        self.state_manager = StateManager()
        self.long_term_knowledge = MemoryManager(model_name="./LLM/models/all-MiniLM-L6-v2")
        self.session_memory = ConversationBufferWindowMemory(
            k=10,  # 进一步减少
            memory_key="chat_history",
            return_messages=True
        )
        
        # 工具组件
        self.file_scanner = None
        self.static_analyzer = StaticAnalysisWrapper()
        
        # Agent组件
        self.bulk_agent = None  # 用于批量静态分析
        self.single_file_agent = None  # 用于单文件手动分析
        self.report_generator = None
        
        # 失败文件处理队列
        self.failed_files_queue = []
        self.processed_files = []
        self.failed_processing = []
        
        print(f"✅ 单文件循环模式编排器 {self.agent_id} 初始化完成")
    
    def analyze_project(self, project_path: str, user_query: str) -> Dict[str, Any]:
        """分析项目的完整流程 - 状态机驱动"""
        print(f"\n{'='*60}")
        print(f"🚀 开始项目架构依赖分析（单文件循环模式）")
        print(f"📁 项目路径: {project_path}")
        print(f"💬 用户需求: {user_query}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        # 创建输出目录
        output_dir = Path(project_path) / ".arch_analysis_results"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 阶段1: 初始化
            self._transition_to(AnalysisPhase.INIT)
            self.file_scanner = FileScanner(project_path)
            
            # 阶段2: 预筛选
            self._transition_to(AnalysisPhase.PRE_SCREENING)
            pre_screened_files = self._perform_pre_screening()
            
            print(f"✅ 预筛选完成：{len(pre_screened_files)} 个潜在架构相关文件\n")
            
            # 阶段3: 批量静态分析
            self._transition_to(AnalysisPhase.STATIC_ANALYSIS)
            static_results = self._perform_static_analysis(
                pre_screened_files, 
                output_dir
            )
            
            # 提取失败文件
            self.failed_files_queue = static_results['failed_files']
            print(f"📊 静态分析完成：")
            print(f"  - 成功: {static_results['success_count']}")
            print(f"  - 失败: {len(self.failed_files_queue)} 个需要手动分析\n")
            
            # 阶段4: 逐个处理失败文件（核心改进）
            if self.failed_files_queue:
                self._transition_to(AnalysisPhase.MANUAL_PROCESSING)
                self._process_failed_files_one_by_one(output_dir)
            
            # 阶段5: 生成报告
            self._transition_to(AnalysisPhase.REPORT_GENERATION)
            final_report = self._generate_final_report(
                project_path, 
                user_query, 
                output_dir,
                start_time
            )
            
            self._transition_to(AnalysisPhase.COMPLETED)
            return final_report
            
        except Exception as e:
            self._transition_to(AnalysisPhase.ERROR)
            print(f"\n❌ 分析过程出错: {e}\n")
            return self._create_error_response(str(e))
    
    def _perform_pre_screening(self) -> List[str]:
        """执行预筛选（静默执行，不占用Agent上下文）"""
        from agents.file_utils import ArchitectureHeuristics
        
        all_files = self.file_scanner.scan_all_files()
        source_files = all_files['source_files']
        
        print(f"🔍 正在对 {len(source_files)} 个文件进行预筛选...")
        
        pre_screened = []
        for file_path in source_files:
            is_arch, _ = ArchitectureHeuristics.is_likely_arch_related(file_path, None)
            if is_arch:
                pre_screened.append(file_path)
        
        return pre_screened
    
    def _perform_static_analysis(
        self, 
        file_list: List[str], 
        output_dir: Path
    ) -> Dict[str, Any]:
        """执行批量静态分析"""
        print(f"⚙️  正在执行静态分析（共 {len(file_list)} 个文件）...\n")
        
        # 创建临时Agent用于静态分析
        tools = [
            StaticAnalysisTool(
                file_scanner=self.file_scanner,
                static_analyzer=self.static_analyzer,
                output_dir=output_dir
            )
        ]
        
        self.bulk_agent = ArchitectureAnalysisAgent(
            llm=self.llm,
            tools=tools,
            output_dir=output_dir,
            verbose=False
        )
        
        # 简化的prompt，只负责调用static_analysis
        context = {
            'project_path': str(self.file_scanner.project_path),
            'pre_screened_files': file_list,
            'source_file_count': len(file_list)
        }
        
        result = self.bulk_agent.analyze(
            user_query="请对预筛选的文件执行静态分析",
            project_context=context
        )
        
        # 解析静态分析结果
        return self._parse_static_analysis_result(output_dir)
    
    def _parse_static_analysis_result(self, output_dir: Path) -> Dict[str, Any]:
        """解析静态分析结果，提取失败文件信息"""
        failed_files = []
        success_count = 0
        
        # 读取所有批次的静态分析结果
        batch_files = list(output_dir.glob("static_analysis_batch_*.json"))
        
        for batch_file in batch_files:
            with open(batch_file, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
                
                for file_path, result in batch_data.items():
                    if result['status'] == 'success':
                        success_count += 1
                    elif result['status'] == 'failed':
                        failed_files.append({
                            'file_path': file_path,
                            'line_number': result.get('line_number', 'unknown'),
                            'error_message': result.get('error_message', ''),
                            'batch_file': batch_file.name
                        })
        
        return {
            'failed_files': failed_files,
            'success_count': success_count
        }
    
    def _process_failed_files_one_by_one(self, output_dir: Path):
        """核心改进：逐个处理失败文件，外部循环控制"""
        total_failed = len(self.failed_files_queue)
        
        print(f"\n{'='*60}")
        print(f"🔧 开始手动补全失败文件（共 {total_failed} 个）")
        print(f"{'='*60}\n")
        
        # 创建单文件专用Agent
        tools = [
            FileReaderTool(
                file_scanner=self.file_scanner,
                max_lines_per_read=100
            ),
            SaveAnalysisResultTool(output_dir=output_dir)
        ]
        
        self.single_file_agent = SingleFileAnalysisAgent(
            llm=self.llm,
            tools=tools,
            output_dir=output_dir,
            verbose=True
        )
        
        # 逐个处理（外部循环）
        for idx, failed_info in enumerate(self.failed_files_queue, 1):
            file_path = failed_info['file_path']
            line_number = failed_info['line_number']
            
            print(f"\n{'─'*60}")
            print(f"📝 处理进度: [{idx}/{total_failed}]")
            print(f"📄 当前文件: {file_path}")
            print(f"❌ 失败行号: {line_number}")
            print(f"{'─'*60}\n")
            
            try:
                # 调用单文件Agent（专注模式）
                result = self.single_file_agent.analyze_single_file(
                    file_path=file_path,
                    error_line=line_number,
                    current_index=idx,
                    total_count=total_failed
                )
                
                if result['status'] == 'success':
                    self.processed_files.append(file_path)
                    print(f"✅ {file_path} 分析完成\n")
                else:
                    self.failed_processing.append({
                        'file': file_path,
                        'reason': result.get('error', 'Unknown')
                    })
                    print(f"⚠️  {file_path} 处理失败: {result.get('error', 'Unknown')}\n")
                
                # 每5个文件后暂停一下，防止API限流
                if idx % 5 == 0 and idx < total_failed:
                    print(f"⏸️  已处理 {idx} 个文件，休息2秒...\n")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ 处理 {file_path} 时出错: {e}\n")
                self.failed_processing.append({
                    'file': file_path,
                    'reason': str(e)
                })
                continue
        
        print(f"\n{'='*60}")
        print(f"✅ 手动补全完成")
        print(f"  - 成功: {len(self.processed_files)}")
        print(f"  - 失败: {len(self.failed_processing)}")
        print(f"{'='*60}\n")
    
    def _generate_final_report(
        self,
        project_path: str,
        user_query: str,
        output_dir: Path,
        start_time: float
    ) -> Dict[str, Any]:
        """生成最终报告"""
        print("📝 正在生成结构化报告...\n")
        
        self.report_generator = ArchitectureReportGenerator(self.llm, output_dir)
        
        # 加载所有分析结果
        all_results = self.report_generator.load_all_analysis_results()
        
        # 统计
        total_analyzed = len(all_results)
        arch_distribution = {}
        for file_info in all_results.values():
            if file_info.get('status') in ['success', 'manual_success']:
                arch = file_info.get('dominant_architecture', 'unknown')
                arch_distribution[arch] = arch_distribution.get(arch, 0) + 1
        
        # 生成agent摘要
        agent_summary = f"""
项目架构分析完成。

**分析统计：**
- 总文件数: {total_analyzed}
- 成功分析: {len(self.processed_files) + len([r for r in all_results.values() if r.get('status') == 'success'])}
- 手动补全: {len(self.processed_files)}
- 处理失败: {len(self.failed_processing)}

**架构分布：**
{json.dumps(arch_distribution, ensure_ascii=False, indent=2)}

详细分析数据已保存到：{output_dir}
"""
        
        structured_report = self.report_generator.generate_structured_report(
            agent_output=agent_summary,
            intermediate_steps=[],
            user_query=user_query
        )
        
        # 组装最终报告
        end_time = time.time()
        execution_time = end_time - start_time
        
        final_report = {
            'project_path': project_path,
            'user_query': user_query,
            'project_statistics': {
                'total_analyzed_files': total_analyzed,
                'manually_processed': len(self.processed_files),
                'processing_failed': len(self.failed_processing),
                'architecture_distribution': arch_distribution
            },
            'agent_summary': agent_summary,
            'structured_report': structured_report.get('structured_report', ''),
            'failed_files': self.failed_processing,
            'data_location': str(output_dir),
            'execution_time': execution_time,
            'generated_at': datetime.now().isoformat()
        }
        
        # 保存最终报告
        report_file = output_dir / "final_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        
        print(f"{'='*60}")
        print(f"✅ 项目分析完成")
        print(f"⏱️  总耗时: {execution_time:.2f} 秒")
        print(f"📊 分析文件: {total_analyzed}")
        print(f"🔧 手动补全: {len(self.processed_files)}")
        print(f"💾 详细数据: {output_dir}")
        print(f"{'='*60}\n")
        
        return final_report
    
    def _transition_to(self, phase: AnalysisPhase):
        """状态转换"""
        print(f"🔄 进入阶段: {phase.value}")
        self.current_phase = phase
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            'status': 'error',
            'error': error_message,
            'current_phase': self.current_phase.value,
            'generated_at': datetime.now().isoformat()
        }


# ============================================================================
# 使用示例
# ============================================================================

def example_usage():
    """示例：单文件循环模式"""
    
    setup_environment()
    
    llm_config = {
        "model": "deepseek-v3:671b",
        "openai_api_key": os.environ["OPENAI_API_KEY"],
        "openai_api_base": os.environ["OPENAI_API_BASE"],
        "temperature": 0.2
    }
    
    orchestrator = ProjectArchitectureOrchestrator(llm_config)
    
    result = orchestrator.analyze_project(
        project_path="LLM/config/eigen",
        user_query="请分析这个项目的架构依赖情况，特别关注 ARM 和 x86 架构的兼容性"
    )
    
    # 打印结果
    print("\n" + "="*60)
    print("📄 最终报告:")
    print("="*60)
    print(result['structured_report'])
    
    if result.get('failed_files'):
        print(f"\n⚠️  有 {len(result['failed_files'])} 个文件处理失败")


if __name__ == "__main__":
    example_usage()