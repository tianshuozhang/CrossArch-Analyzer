"""
项目架构分析编排器 - 修复版
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict
import json
import time
from datetime import datetime
from enum import Enum

current_dir = os.path.dirname(os.path.abspath(__file__))
LLM_dir = os.path.dirname(current_dir)
sys.path.append(LLM_dir)

from langchain_openai import ChatOpenAI
from agents.file_utils import FileScanner, ArchitectureHeuristics
from agents.static_tool_wrapper import StaticAnalysisWrapper
from agents.agent_tools import (
    FileReaderTool,
    StaticAnalysisTool,
    SaveAnalysisResultTool
)
from agents.agent_core import (
    ArchitectureAnalysisAgent,
    WholeFileAnalysisAgent,
    ArchitectureReportGenerator
)
from core.state_manager import StateManager
from core.memory_manager import MemoryManager
from langchain_classic.memory import ConversationBufferWindowMemory
from utils import setup_environment


class AnalysisPhase(Enum):
    """分析阶段"""
    INIT = "init"
    PRE_SCREENING = "pre_screening"
    STATIC_ANALYSIS = "static_analysis"
    MANUAL_PROCESSING = "manual_processing"
    REPORT_GENERATION = "report_generation"
    COMPLETED = "completed"
    ERROR = "error"


class FileTask:
    """文件级任务"""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.error_regions = []
        self.status = 'pending'
        self.result = None
        self.is_from_static_analysis = False
    
    def add_region(self, region_info: Dict[str, Any]):
        self.error_regions.append(region_info)
    
    def has_errors(self) -> bool:
        return len(self.error_regions) > 0
    
    def __repr__(self):
        return f"FileTask({self.file_path}, {len(self.error_regions)} 个区间)"


class ProjectArchitectureOrchestrator:
    """项目架构分析编排器"""
    
    def __init__(
        self, 
        llm_config: Dict[str, Any], 
        agent_id: str = "arch_agent_001",
        use_agent_for_static_analysis: bool = False
    ):
        """
        Args:
            llm_config: LLM配置
            agent_id: Agent ID
            use_agent_for_static_analysis: 是否使用Agent进行静态分析
                - True: 让大模型调用静态分析工具
                - False: 直接在代码中调用静态分析
        """
        self.agent_id = agent_id
        self.llm = ChatOpenAI(**llm_config)
        self.use_agent_for_static_analysis = use_agent_for_static_analysis
        self.current_phase = AnalysisPhase.INIT
        
        # 状态管理
        self.state_manager = StateManager()
        self.long_term_knowledge = MemoryManager(model_name="./LLM/models/all-MiniLM-L6-v2")
        self.session_memory = ConversationBufferWindowMemory(
            k=10,
            memory_key="chat_history",
            return_messages=True
        )
        
        # 核心数据结构
        self.file_tasks = {}
        self.processed_tasks = []
        self.failed_tasks = []
        
        # 统计信息
        self.stats = {
            'total_pre_screened': 0,
            'static_success': 0,
            'static_failed': 0,
            'manual_success': 0,
            'manual_failed': 0
        }
        
        # 组件
        self.file_scanner = None
        self.static_analyzer = None
        self.bulk_agent = None
        self.whole_file_agent = None
        self.report_generator = None
        
        mode_text = "Agent模式" if use_agent_for_static_analysis else "直接调用模式"
        print(f"✅ 编排器 {self.agent_id} 初始化完成（静态分析: {mode_text}）")
    
    def analyze_project(self, project_path: str, user_query: str) -> Dict[str, Any]:
        """完整分析流程"""
        print(f"\n{'='*60}")
        print(f"🚀 开始项目架构依赖分析")
        print(f"📁 项目路径: {project_path}")
        print(f"💬 用户需求: {user_query}")
        print(f"⚙️  静态分析模式: {'Agent调用' if self.use_agent_for_static_analysis else '直接调用'}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        output_dir = Path(project_path) / ".arch_analysis_results"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 阶段1: 初始化
            self._transition_to(AnalysisPhase.INIT)
            self._initialize_components(project_path)
            
            # 阶段2: 预筛选
            self._transition_to(AnalysisPhase.PRE_SCREENING)
            pre_screened_files = self._perform_pre_screening()
            self.stats['total_pre_screened'] = len(pre_screened_files)
            
            print(f"✅ 预筛选完成：{len(pre_screened_files)} 个潜在架构相关文件\n")
            
            # 阶段3: 静态分析（根据模式选择）
            self._transition_to(AnalysisPhase.STATIC_ANALYSIS)
            if self.use_agent_for_static_analysis:
                self._perform_agent_static_analysis(pre_screened_files, output_dir)
            else:
                self._perform_direct_static_analysis(pre_screened_files, output_dir)
            
            # 阶段4: 按文件处理
            manual_files = [task for task in self.file_tasks.values() if task.has_errors()]
            
            if manual_files:
                self._transition_to(AnalysisPhase.MANUAL_PROCESSING)
                self._process_files_with_all_regions(manual_files, output_dir)
            
            # 阶段5: 生成报告
            self._transition_to(AnalysisPhase.REPORT_GENERATION)
            final_report = self._generate_final_report(
                project_path, user_query, output_dir, start_time
            )
            
            self._transition_to(AnalysisPhase.COMPLETED)
            return final_report
            
        except Exception as e:
            self._transition_to(AnalysisPhase.ERROR)
            print(f"\n❌ 分析过程出错: {e}\n")
            import traceback
            traceback.print_exc()
            return self._create_error_response(str(e))
    
    def _initialize_components(self, project_path: str):
        """初始化扫描器和分析器"""
        self.file_scanner = FileScanner(project_path)
        self.static_analyzer = StaticAnalysisWrapper(region_size=100)
        print(f"✅ 组件初始化完成\n")
    
    def _perform_pre_screening(self) -> List[str]:
        """执行预筛选"""
        all_files = self.file_scanner.scan_all_files()
        source_files = all_files['source_files']
        
        print(f"🔍 正在对 {len(source_files)} 个文件进行预筛选...")
        
        pre_screened = []
        for file_path in source_files:
            is_arch, _ = ArchitectureHeuristics.is_likely_arch_related(file_path, None)
            if is_arch:
                pre_screened.append(file_path)
        
        return pre_screened
    
    def _perform_agent_static_analysis(
        self, 
        pre_screened_files: List[str], 
        output_dir: Path
    ):
        """使用Agent进行静态分析"""
        print(f"⚙️  使用Agent进行静态分析（共 {len(pre_screened_files)} 个文件）...\n")
        
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
        
        context = {
            'project_path': str(self.file_scanner.project_path),
            'pre_screened_files': pre_screened_files,
            'source_file_count': len(pre_screened_files)
        }
        
        result = self.bulk_agent.analyze(
            user_query="请对预筛选的文件执行静态分析",
            project_context=context
        )
        
        # 等待Agent执行完成并保存结果
        time.sleep(1)
        
        # 解析结果
        self._parse_static_analysis_result_from_files(output_dir)
    
    def _perform_direct_static_analysis(
        self, 
        pre_screened_files: List[str], 
        output_dir: Path
    ):
        """直接调用静态分析"""
        print(f"⚙️  直接执行静态分析（共 {len(pre_screened_files)} 个文件）...\n")
        
        # 批量读取文件
        files_content = self.file_scanner.batch_read_files(pre_screened_files)
        
        # 批量分析
        analysis_results = self.static_analyzer.batch_analyze_files(files_content)
        
        # 保存详细结果
        batch_file = output_dir / "static_analysis_batch_1.json"
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)
        
        # 创建文件任务
        self._process_analysis_results(analysis_results)
        
        print(f"\n📊 静态分析完成：")
        print(f"  ✅ 成功: {self.stats['static_success']} 个文件")
        print(f"  ⚠️  失败: {self.stats['static_failed']} 个文件")
        
        total_regions = sum(
            len(task.error_regions) 
            for task in self.file_tasks.values() 
            if task.has_errors()
        )
        print(f"  🔍 总错误区间数: {total_regions}\n")
    
    def _process_analysis_results(self, analysis_results: Dict[str, Dict[str, Any]]):
        """处理分析结果并创建任务"""
        for file_path, result in analysis_results.items():
            task = FileTask(file_path)
            
            if result['status'] == 'success':
                task.status = 'success'
                task.result = result
                self.stats['static_success'] += 1
                self.processed_tasks.append(task)
                
            elif result['status'] == 'failed':
                task.status = 'pending'
                task.is_from_static_analysis = True
                
                for region_info in result.get('error_regions', []):
                    task.add_region(region_info)
                
                self.stats['static_failed'] += 1
            
            elif result['status'] == 'error':
                task.status = 'pending'
                task.is_from_static_analysis = True
                self.stats['static_failed'] += 1
            
            self.file_tasks[file_path] = task
    
    def _parse_static_analysis_result_from_files(self, output_dir: Path):
        """从保存的文件中解析Agent模式的静态分析结果"""
        print(f"\n📂 正在解析静态分析结果...\n")
        
        batch_files = list(output_dir.glob("static_analysis_batch_*.json"))
        
        if not batch_files:
            print(f"⚠️  警告：未找到静态分析结果文件\n")
            return
        
        all_results = {}
        
        for batch_file in batch_files:
            try:
                with open(batch_file, 'r', encoding='utf-8') as f:
                    batch_data = json.load(f)
                    all_results.update(batch_data)
            except Exception as e:
                print(f"⚠️  读取 {batch_file.name} 失败: {e}")
                continue
        
        if all_results:
            self._process_analysis_results(all_results)
            
            print(f"📊 静态分析完成：")
            print(f"  ✅ 成功: {self.stats['static_success']} 个文件")
            print(f"  ⚠️  失败: {self.stats['static_failed']} 个文件")
            
            total_regions = sum(
                len(task.error_regions) 
                for task in self.file_tasks.values() 
                if task.has_errors()
            )
            print(f"  🔍 总错误区间数: {total_regions}\n")
        else:
            print(f"⚠️  警告：静态分析结果为空\n")
    
    def _process_files_with_all_regions(
        self, 
        file_tasks: List[FileTask], 
        output_dir: Path
    ):
        """按文件处理所有区间"""
        total_files = len(file_tasks)
        
        print(f"\n{'='*60}")
        print(f"🔧 开始按文件手动分析（共 {total_files} 个文件）")
        print(f"{'='*60}\n")
        
        tools = [
            FileReaderTool(
                file_scanner=self.file_scanner,
                max_lines_per_read=200
            ),
            SaveAnalysisResultTool(output_dir=output_dir)
        ]
        
        self.whole_file_agent = WholeFileAnalysisAgent(
            llm=self.llm,
            tools=tools,
            output_dir=output_dir,
            verbose=True
        )
        from tqdm import tqdm
        for file_idx, file_task in tqdm(enumerate(file_tasks, 1), total=total_files, desc="处理文件"):
            total_regions = len(file_task.error_regions)
            
            print(f"\n{'─'*60}")
            print(f"📝 进度: [{file_idx}/{total_files}] ({file_idx/total_files*100:.1f}%)")
            print(f"📄 文件: {file_task.file_path}")
            print(f"🔍 错误区间数: {total_regions}")
            print(f"{'─'*60}\n")
            
            try:
                file_task.status = 'processing'
                
                result = self.whole_file_agent.analyze_whole_file(
                    file_path=file_task.file_path,
                    all_error_regions=file_task.error_regions,
                    file_index=file_idx,
                    total_files=total_files
                )
                
                if result['status'] == 'success':
                    file_task.status = 'success'
                    file_task.result = result
                    self.processed_tasks.append(file_task)
                    self.stats['manual_success'] += 1
                    print(f"✅ 文件分析完成\n")
                else:
                    file_task.status = 'failed'
                    file_task.result = result
                    self.failed_tasks.append(file_task)
                    self.stats['manual_failed'] += 1
                    print(f"⚠️  文件处理失败: {result.get('error', 'Unknown')}\n")
                
                if file_idx % 3 == 0 and file_idx < total_files:
                    print(f"⏸️  已处理 {file_idx} 个文件，休息2秒...\n")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ 处理文件时出错: {e}\n")
                file_task.status = 'failed'
                self.failed_tasks.append(file_task)
                self.stats['manual_failed'] += 1
                continue
        
        print(f"\n{'='*60}")
        print(f"✅ 文件分析完成")
        print(f"  - 成功: {self.stats['manual_success']} 个文件")
        print(f"  - 失败: {self.stats['manual_failed']} 个文件")
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
        
        all_results = self.report_generator.load_all_analysis_results()
        
        total_analyzed = len(all_results)
        arch_distribution = {}
        for file_info in all_results.values():
            if file_info.get('status') in ['success', 'manual_success']:
                arch = file_info.get('dominant_architecture', 'unknown')
                arch_distribution[arch] = arch_distribution.get(arch, 0) + 1
        
        agent_summary = f"""
项目架构分析完成。

**文件级统计：**
- 预筛选文件数: {self.stats['total_pre_screened']}
- 静态分析成功: {self.stats['static_success']}
- 手动分析成功: {self.stats['manual_success']}
- 总分析文件数: {total_analyzed}

**架构分布：**
{json.dumps(arch_distribution, ensure_ascii=False, indent=2)}

详细分析数据已保存到：{output_dir}
"""
        
        structured_report = self.report_generator.generate_structured_report(
            agent_output=agent_summary,
            intermediate_steps=[],
            user_query=user_query
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        final_report = {
            'project_path': project_path,
            'user_query': user_query,
            'analysis_mode': 'agent_static' if self.use_agent_for_static_analysis else 'direct_static',
            'project_statistics': {
                'total_pre_screened': self.stats['total_pre_screened'],
                'static_success': self.stats['static_success'],
                'static_failed': self.stats['static_failed'],
                'manual_success': self.stats['manual_success'],
                'manual_failed': self.stats['manual_failed'],
                'total_analyzed': total_analyzed,
                'architecture_distribution': arch_distribution
            },
            'agent_summary': agent_summary,
            'structured_report': structured_report.get('structured_report', ''),
            'failed_files': [
                {
                    'file': task.file_path,
                    'regions': len(task.error_regions),
                    'error': task.result.get('error') if task.result else 'Unknown'
                }
                for task in self.failed_tasks
            ],
            'data_location': str(output_dir),
            'execution_time': execution_time,
            'generated_at': datetime.now().isoformat()
        }
        
        report_file = output_dir / "final_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        
        print(f"{'='*60}")
        print(f"✅ 项目分析完成")
        print(f"⏱️  总耗时: {execution_time:.2f} 秒")
        print(f"📊 预筛选: {self.stats['total_pre_screened']}")
        print(f"✅ 静态成功: {self.stats['static_success']}")
        print(f"🔧 手动成功: {self.stats['manual_success']}")
        print(f"❌ 总失败: {len(self.failed_tasks)}")
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


def example_usage():
    """使用示例"""
    setup_environment()
    
    llm_config = {
        "model": "deepseek-v3:671b",
        "openai_api_key": os.environ["OPENAI_API_KEY"],
        "openai_api_base": os.environ["OPENAI_API_BASE"],
        "temperature": 0.2
    }
    
    # 推荐使用直接调用模式（更可靠）
    orchestrator = ProjectArchitectureOrchestrator(
        llm_config, 
        use_agent_for_static_analysis=False
    )
    
    result = orchestrator.analyze_project(
        project_path="LLM/config/eigen",
        user_query="请分析这个项目的架构依赖情况"
    )


if __name__ == "__main__":
    example_usage()