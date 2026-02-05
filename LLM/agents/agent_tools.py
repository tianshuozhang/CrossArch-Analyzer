"""
Agent 工具模块 - 优化版：减少上下文占用，添加文件保存功能
"""
from langchain.tools import BaseTool
from typing import Dict, Any, List, Optional
from pydantic import Field, BaseModel
import json
import os
from pathlib import Path

from agents.file_utils import FileScanner, ArchitectureHeuristics
from agents.static_tool_wrapper import StaticAnalysisWrapper
from tqdm import tqdm

# ============= 输入模型定义 =============
class ProjectInfoInput(BaseModel):
    info_type: str = Field(description="获取信息的类型，可选: 'file_list', 'build_files', 'file_tree', 'summary'")

class FileReaderInput(BaseModel):
    file_path: str = Field(description="要读取的文件相对路径")
    start_line: int = Field(default=None, description="起始行号")
    end_line: int = Field(default=None, description="结束行号")

class FileScreeningInput(BaseModel):
    file_paths: List[str] = Field(description="要进行架构相关性筛选的文件路径列表")
    include_content: bool = Field(default=False, description="是否需要检查文件内容")

class StaticAnalysisInput(BaseModel):
    file_paths: List[str] = Field(description="要进行深度静态分析的文件路径列表")
    batch_size: int = Field(default=50, description="单批次处理文件数量，默认50")

class SaveResultInput(BaseModel):
    data_type: str = Field(description="数据类型标识，如'manual_analysis', 'screening_results'等")
    data: Dict[str, Any] = Field(description="要保存的数据字典")


# ============= 新增：结果保存工具 =============
class SaveAnalysisResultTool(BaseTool):
    """将分析结果保存到JSON文件，避免占用上下文"""
    
    name: str = "save_analysis_result"
    description: str = """
    将分析结果保存到JSON文件，用于：
    1. 手动补全的架构分析结果
    2. 中间处理数据
    3. 任何不需要在上下文中保留的大型数据
    
    输入参数:
    - data_type: 数据类型标识（如 'manual_analysis', 'batch_1_results'）
    - data: 要保存的数据字典
    
    返回: 保存的文件路径
    
    示例:
    {
        "data_type": "manual_analysis",
        "data": {
            "file1.c": {"arch_related_blocks": [...]}
        }
    }
    """
    args_schema: type[BaseModel] = SaveResultInput
    output_dir: Path = Field(exclude=True)
    
    def _run(self, data_type: str, data: Dict[str, Any]) -> str:
        """保存数据到JSON文件"""
        try:
            # 生成文件名
            filename = f"{data_type}.json"
            filepath = self.output_dir / filename
            
            # 确保目录存在
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            result = {
                'status': 'success',
                'filepath': str(filepath),
                'data_type': data_type,
                'size_kb': os.path.getsize(filepath) / 1024
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)


# ============= 优化：文件筛选工具 =============
class FileScreeningTool(BaseTool):
    """文件架构相关性筛选工具 - 优化版"""
    
    name: str = "file_screening"
    description: str = """
    使用启发式规则判断文件是否可能包含架构相关代码。
    返回精简的筛选结果，不包含详细原因。
    
    输入: {"file_paths": ["src/file1.c", "src/file2.c"], "include_content": false}
    输出: 架构相关文件列表和统计信息
    """
    args_schema: type[BaseModel] = FileScreeningInput
    file_scanner: FileScanner = Field(exclude=True)
    
    def _run(self, file_paths: List[str], include_content: bool = False) -> str:
        try:
            arch_related = []
            arch_free = []
            print("🔍 正在筛选架构相关文件...")
            print(file_paths)
            for file_path in tqdm(file_paths):
                is_arch, reasons = ArchitectureHeuristics.is_likely_arch_related(
                    file_path, None
                )
                
                if is_arch:
                    arch_related.append(file_path)
                else:
                    arch_free.append(file_path)
            
            result = {
                'arch_related_files': arch_related,
                'arch_free_count': len(arch_free),
                'total_checked': len(file_paths),
                'summary': f"发现 {len(arch_related)}/{len(file_paths)} 个可能架构相关"
            }
            print(result)
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({'error': str(e)}, ensure_ascii=False)


# ============= 优化：静态分析工具（精简输出）=============
class StaticAnalysisTool(BaseTool):
    """静态代码分析工具 - 优化版：自动保存详细结果，只返回摘要"""
    
    name: str = "static_analysis"
    description: str = """
    对C/C++源文件进行深度静态分析。
    
    【重要】此工具会自动保存详细结果到文件，只返回：
    1. 总体统计信息
    2. 失败文件列表及建议的行号范围
    
    支持分批处理，避免单次分析过多文件。
    
    输入: {"file_paths": ["file1.c"], "batch_size": 50}
    """
    args_schema: type[BaseModel] = StaticAnalysisInput
    file_scanner: FileScanner = Field(exclude=True)
    static_analyzer: StaticAnalysisWrapper = Field(exclude=True)
    output_dir: Path = Field(exclude=True)
    
    def _run(self, file_paths: List[str], batch_size: int = 50) -> str:
        try:
            if not file_paths:
                return json.dumps({'error': '未提供要分析的文件'}, ensure_ascii=False)
            
            # 分批处理
            all_batches_summary = []
            total_success = 0
            total_failed = 0
            failed_files_info = []
            
            for i in range(0, len(file_paths), batch_size):
                batch = file_paths[i:i+batch_size]
                batch_num = i // batch_size + 1
                
                # 分析当前批次
                files_content = self.file_scanner.batch_read_files(batch)
                analysis_results = self.static_analyzer.batch_analyze_files(files_content)
                
                # 保存详细结果到文件
                batch_filename = f"static_analysis_batch_{batch_num}.json"
                batch_filepath = self.output_dir / batch_filename
                self.output_dir.mkdir(parents=True, exist_ok=True)
                
                with open(batch_filepath, 'w', encoding='utf-8') as f:
                    json.dump(analysis_results, f, ensure_ascii=False, indent=2)
                
                # 统计本批次结果
                batch_success = sum(1 for r in analysis_results.values() if r['status'] == 'success')
                batch_failed = len(analysis_results) - batch_success
                
                total_success += batch_success
                total_failed += batch_failed
                
                # 收集失败文件信息（只保留关键信息）
                for file_path, result in analysis_results.items():
                    if result['status'] == 'failed':
                        failed_line = result.get('line_number', 'unknown')
                        failed_files_info.append({
                            'file': file_path,
                            'line': failed_line,
                            'batch': batch_num
                        })
                
                all_batches_summary.append({
                    'batch': batch_num,
                    'files': len(batch),
                    'success': batch_success,
                    'failed': batch_failed,
                    'saved_to': batch_filename
                })
            
            # 返回精简摘要
            output = {
                'status': 'completed',
                'total_files': len(file_paths),
                'total_success': total_success,
                'total_failed': total_failed,
                'batches': all_batches_summary,
                'failed_files': failed_files_info[:10],  # 最多返回10个失败案例
                'instruction': f"详细结果已保存到 {len(all_batches_summary)} 个文件。"
                              f"对于失败的文件，请用 read_file 读取建议行号范围进行手动分析，"
                              f"并用 save_analysis_result 保存补全数据。"
            }
            
            return json.dumps(output, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({'status': 'error', 'message': str(e)}, ensure_ascii=False)


# ============= 优化：文件读取工具（限制单次读取）=============
class FileReaderTool(BaseTool):
    """文件内容读取工具 - 强制限制读取行数"""
    
    name: str = "read_file"
    description: str = """
    读取文件内容片段。
    
    【强制约束】单次读取不超过100行，必须指定 start_line 和 end_line。
    """
    args_schema: type[BaseModel] = FileReaderInput
    file_scanner: FileScanner = Field(exclude=True)
    max_lines_per_read: int = Field(default=100, exclude=True)

    def _run(self, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
        try:
            # 强制要求指定行号范围
            if start_line is None or end_line is None:
                return json.dumps({
                    'status': 'error',
                    'error': '必须指定 start_line 和 end_line。单次读取不超过100行。'
                }, ensure_ascii=False)
            
            # 检查行数限制
            if end_line - start_line + 1 > self.max_lines_per_read:
                return json.dumps({
                    'status': 'error',
                    'error': f'请求行数 {end_line - start_line + 1} 超过限制 {self.max_lines_per_read}。请缩小范围。'
                }, ensure_ascii=False)
            
            content = self.file_scanner.read_file(
                relative_path=file_path, 
                start_line=start_line, 
                end_line=end_line
            )
            
            if content is None:
                return json.dumps({
                    'status': 'error',
                    'error': f'无法读取文件: {file_path}'
                }, ensure_ascii=False)
            
            response = {
                'file_path': file_path,
                'range': f"{start_line}-{end_line}",
                'content': content
            }
            
            return json.dumps(response, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)


# ============= ProjectInfoTool（不变）=============
class ProjectInfoTool(BaseTool):
    """项目信息查询工具"""
    
    name: str = "get_project_info"
    description: str = """
    获取项目基本信息。
    输入: {"info_type": "summary"}  # 可选: file_list, build_files, summary
    """
    args_schema: type[BaseModel] = ProjectInfoInput
    file_scanner: FileScanner = Field(exclude=True)
    all_files: Dict[str, List[str]] = Field(exclude=True)
    file_tree: str = Field(exclude=True, default="")
    
    def _run(self, info_type: str) -> str:
        try:
            if info_type == 'file_list':
                return json.dumps({
                    'source_files': self.all_files['source_files'],
                    'count': len(self.all_files['source_files'])
                }, ensure_ascii=False, indent=2)
            
            elif info_type == 'build_files':
                return json.dumps({
                    'build_files': self.all_files['build_files'],
                    'doc_files': self.all_files['doc_files']
                }, ensure_ascii=False, indent=2)
            
            elif info_type == 'summary':
                return json.dumps({
                    'total_source_files': len(self.all_files['source_files']),
                    'build_files': self.all_files['build_files'],
                    'doc_files': self.all_files['doc_files']
                }, ensure_ascii=False, indent=2)
            
            else:
                return json.dumps({'error': f'未知的 info_type: {info_type}'}, ensure_ascii=False)
                
        except Exception as e:
            return json.dumps({'error': str(e)}, ensure_ascii=False)