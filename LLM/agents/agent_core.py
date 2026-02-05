"""
单文件区间分析Agent - 支持一个文件多个区间
"""
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any, List
import json
from pathlib import Path

"""
整文件分析Agent - 完整实现
添加到 agents/agent_core.py 中
"""
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from typing import Dict, Any, List
import json
from pathlib import Path


class WholeFileAnalysisAgent:
    """整文件架构分析Agent"""
    
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
        
        self.executor = create_react_agent(
            model=self.llm,
            tools=self.tools
        )
    
    def analyze_whole_file(
        self,
        file_path: str,
        all_error_regions: List[Dict[str, Any]],
        file_index: int,
        total_files: int
    ) -> Dict[str, Any]:
        """分析单个文件的所有错误区间"""
        
        prompt = self._create_whole_file_prompt(
            file_path, all_error_regions, file_index, total_files
        )
        
        if self.verbose:
            print(f"🤖 开始分析文件: {file_path}（{len(all_error_regions)} 个区间）")
        
        try:
            result = self.executor.invoke(
                {"messages": [HumanMessage(content=prompt)]},
                config={"recursion_limit": 25}
            )
            
            final_message = result["messages"][-1]
            output_text = final_message.content
            
            if self._verify_file_analysis_saved(file_path,file_index):
                return {
                    'status': 'success',
                    'file': file_path,
                    'regions_count': len(all_error_regions),
                    'output': output_text
                }
            else:
                print(f"⚠️ 文件分析结果未保存: {file_path}")
                print("🤖 Agent 输出:")
                print(output_text)
                return {
                    'status': 'failed',
                    'file': file_path,
                    'error': '文件分析结果未保存',
                    'output': output_text
                }
            
        except Exception as e:
            return {
                'status': 'error',
                'file': file_path,
                'error': str(e)
            }
    
    def _create_whole_file_prompt(
        self,
        file_path: str,
        all_error_regions: List[Dict[str, Any]],
        file_index: int,
        total_files: int
    ) -> str:
        """创建整文件分析的prompt"""
        
        progress_percent = file_index / total_files * 100
        progress_bar_length = 20
        filled = int(progress_percent / 100 * progress_bar_length)
        progress_bar = '█' * filled + '░' * (progress_bar_length - filled)
        
        regions_summary = []
        for i, region in enumerate(all_error_regions, 1):
            start = region['start_line']
            end = region['end_line']
            error_lines = region['error_lines']
            
            if len(error_lines) <= 5:
                error_str = ", ".join(map(str, error_lines))
            else:
                error_str = ", ".join(map(str, error_lines[:5])) + f"... (共{len(error_lines)}个)"
            
            regions_summary.append(
                f"  区间 {i}: 第 {start}-{end} 行 (报错行: {error_str})"
            )
        
        regions_text = "\n".join(regions_summary)
        
        prompt = f"""# 🎯 整文件架构分析任务

## 📊 任务进度
```
全局进度: [{file_index}/{total_files}] {progress_bar} {progress_percent:.1f}%
当前任务: 第 {file_index} 个文件（共 {total_files} 个）
完成度: {file_index-1} 已完成 | 1 进行中 | {total_files-file_index} 待处理
```

## 🎯 当前文件分析

**文件路径:** `{file_path}`  
**错误区间数:** {len(all_error_regions)} 个

### 错误区间列表：
```
{regions_text}
```

---

## 📝 执行策略

### 🔑 核心要求：一次性分析该文件的**所有**区间

你需要：
1. 依次读取每个错误区间的代码
2. 分析每个区间的架构依赖
3. 汇总整个文件的架构信息
4. **一次性保存**该文件的完整分析结果

---

## 🔍 具体步骤

### 步骤1: 逐区间读取代码

对于每个区间，使用 `read_file` 工具：

```python
# 区间1
read_file(
    file_path="{file_path}",
    start_line={all_error_regions[0]['start_line']},
    end_line={all_error_regions[0]['end_line']}
)

# 区间2（如果有）
# read_file(file_path="{file_path}", start_line=..., end_line=...)

# ... 依此类推
```

⚠️ **注意**: 
- 如果区间超过200行，可以分两次读取
- 重点关注报错行附近的代码

---

### 步骤2: 分析每个区间

对于每个区间，识别：

**架构特定宏:**
- ARM: `__ARM_NEON`, `__ARM_ARCH`, `__aarch64__`
- x86: `__SSE__`, `__AVX__`, `__x86_64__`, `_M_X64`
- RISC-V: `__riscv`, `__riscv_xlen`

**内联汇编:**
```c
__asm__ volatile("mov r0, r1");  // ARM
asm("movq %rax, %rbx");          // x86
```

**SIMD Intrinsics:**
- ARM NEON: `vaddq_u8()`, `vmulq_f32()`, `vld1q_*`
- x86 SSE/AVX: `_mm_add_ps()`, `_mm256_mul_pd()`

**条件编译:**
```c
#ifdef __ARM_NEON
    // ARM NEON code
#elif defined(__AVX__)
    // x86 AVX code
#endif
```

---

### 步骤3: 汇总并保存结果（必须）
读取完这个文件的所有区间后，调用名为`save_analysis_result`的SaveAnalysisResultTool进行**一次性保存**：
注意保存路径一定是 `manual_file_{file_index}.json`。
```python
save_analysis_result(
    data_type="manual_file_{file_index}",
    data={{
        "{file_path}": {{
            "status": "manual_success",
            "dominant_architecture": "ARM/x86/RISC-V/Generic",
            "all_architectures": ["ARM_NEON", "x86_SSE"],
            "total_regions_analyzed": {len(all_error_regions)},
            "arch_related_blocks": [
                {{
                    "region_index": 1,
                    "start_line": ...,
                    "end_line": ...,
                    "architecture": "ARM_NEON",
                    "code_fragment": "关键代码片段（1-2行）",
                    "reason": "判断理由"
                }},
                {{
                    "region_index": 2,
                    "start_line": ...,
                    "end_line": ...,
                    "architecture": "x86_SSE",
                    "code_fragment": "...",
                    "reason": "..."
                }},
                // ... 所有区间的所有架构块
            ]
        }}
    }}
)
```

**关键点:**
1. `arch_related_blocks` 包含**所有区间**的所有架构块
2. 每个块标记它来自哪个区间（`region_index`）
3. `dominant_architecture` 是出现最多的架构
4. `all_architectures` 是该文件涉及的所有架构

---

### 步骤4: 完成标记（必须）

保存完成后，回复：

```
✅ 已完成 {file_path} 的完整分析
  - 分析区间数: {len(all_error_regions)}
  - 发现架构: [列出]
  - 保存文件路径： manual_file_{file_path.replace('/', '_')}.json
```

---

## ⚠️ 重要约束

1. **必须读取所有区间** - 不要遗漏任何区间
2. **只保存一次** - 将所有区间的结果合并后保存
3. **明确标记** - 每个架构块标明来自哪个区间
4. **简洁回复** - 不要输出完整代码

---

## 💡 分析提示

**合并策略:**
- 如果多个区间都是同一种架构（如都是ARM NEON），在 `dominant_architecture` 中体现
- 如果不同区间涉及不同架构（如区间1是ARM，区间2是x86），在 `all_architectures` 中列出所有

**区间关联:**
- 某些区间可能是同一个条件编译块的不同部分
- 注意检查区间之间的代码是否有关联

---

## 🚀 开始执行

现在开始分析 `{file_path}` 的 {len(all_error_regions)} 个错误区间。

**执行顺序：**
1. 读取区间1的代码
2. 读取区间2的代码（如果有）
3. ...
4. 分析所有区间，汇总结果
5. 一次性保存

开始！
"""
        
        return prompt
    
    def _verify_file_analysis_saved(self, file_path: str, file_index: int) -> bool:
        """验证文件分析结果是否已保存"""
        # safe_filename = file_path.replace('/', '_').replace('\\', '_')
        pattern = f"manual_file_{file_index}.json"
        
        analysis_files = list(self.output_dir.glob(pattern))
        
        if analysis_files:
            try:
                with open(analysis_files[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if file_path in data:
                        file_data = data[file_path]
                        required_fields = ['status', 'dominant_architecture', 'arch_related_blocks']
                        if all(field in file_data for field in required_fields):
                            return True
            except Exception as e:
                print(f"⚠️ 验证文件分析结果失败: {e}")
                raise e
                
        
        return False

# 保留原有的批量静态分析Agent
class ArchitectureAnalysisAgent:
    """批量静态分析 Agent"""
    
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
        
        self.executor = create_react_agent(
            model=self.llm,
            tools=self.tools
        )
    
    def analyze(self, user_query: str, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """执行批量静态分析"""
        
        input_text = f"""
# 批量静态分析任务

**项目路径:** {project_context['project_path']}
**待分析文件:** {len(project_context['pre_screened_files'])} 个

## 你的任务

调用 `static_analysis` 工具对文件进行分析：

```python
static_analysis(
    file_paths={project_context['pre_screened_files']},
    batch_size=50
)
```

工具会自动：
1. 分批处理文件
2. 保存详细结果到JSON
3. 返回统计摘要和失败文件的错误区间列表

你只需调用工具，然后总结返回的结果即可。**不要尝试处理失败文件。**
"""
        
        try:
            result = self.executor.invoke(
                {"messages": [HumanMessage(content=input_text)]},
                config={"recursion_limit": 20}
            )
            
            final_message = result["messages"][-1]
            
            return {
                'status': 'success',
                'output': final_message.content,
                'intermediate_steps': result["messages"]
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'output': f"批量分析失败: {e}"
            }


class ArchitectureReportGenerator:
    """报告生成器 - 支持区间级别的结果合并"""
    
    def __init__(self, llm: ChatOpenAI, output_dir: Path):
        self.llm = llm
        self.output_dir = output_dir
    
    def load_all_analysis_results(self) -> Dict[str, Any]:
        """从保存的JSON文件中加载所有分析结果（包括区间级和合并后的文件级）"""
        combined_results = {}
        
        # 1. 读取静态分析批次结果（成功的文件）
        batch_files = list(self.output_dir.glob("static_analysis_batch_*.json"))
        for batch_file in batch_files:
            try:
                with open(batch_file, 'r', encoding='utf-8') as f:
                    batch_data = json.load(f)
                    # 只保留成功的文件
                    for file_path, result in batch_data.items():
                        if result.get('status') == 'success':
                            combined_results[file_path] = result
            except Exception as e:
                print(f"⚠️  读取 {batch_file} 失败: {e}")
        
        # 2. 读取合并后的手动分析结果（优先级最高）
        merged_file = self.output_dir / "manual_analysis_merged.json"
        if merged_file.exists():
            try:
                with open(merged_file, 'r', encoding='utf-8') as f:
                    merged_data = json.load(f)
                    # 覆盖或添加手动分析的结果
                    combined_results.update(merged_data)
            except Exception as e:
                print(f"⚠️  读取合并结果失败: {e}")
        
        return combined_results
    
    def generate_structured_report(
        self,
        agent_output: str,
        intermediate_steps: List[Any],
        user_query: str
    ) -> Dict[str, Any]:
        """生成结构化报告"""
        
        raw_dependencies = self.extract_dependency_blocks()
        
        # 统计信息
        total_files = len(raw_dependencies)
        arch_distribution = {}
        for file_info in raw_dependencies.values():
            arch = file_info['dominant_architecture']
            arch_distribution[arch] = arch_distribution.get(arch, 0) + 1
        
        # 使用LLM生成最终报告
        system_prompt = """你是技术报告编写专家。根据架构分析结果生成清晰的报告。

报告结构（Markdown格式）：
1. **执行摘要** - 项目架构类型和关键发现
2. **架构分布** - 各架构的文件数量和占比
3. **风险评估** - 移植性风险等级（低/中/高）
4. **优化建议** - 具体改进方案

简洁专业，不要包含原始代码。"""

        human_prompt = f"""
**用户需求:** {user_query}

**分析统计:**
- 分析文件总数: {total_files}
- 架构分布: {json.dumps(arch_distribution, ensure_ascii=False)}

**Agent执行摘要:**
{agent_output[:300]}...

请生成结构化报告（不要包含原始代码片段）。"""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ])
            
            return {
                'structured_report': response.content,
                'raw_dependency_data': raw_dependencies,
                'statistics': {
                    'total_analyzed_files': total_files,
                    'architecture_distribution': arch_distribution
                },
                'data_location': str(self.output_dir)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'raw_dependency_data': raw_dependencies
            }
    
    def extract_dependency_blocks(self) -> Dict[str, Any]:
        """从文件中提取架构依赖块信息"""
        all_results = self.load_all_analysis_results()
        dependency_map = {}
        
        for file_path, info in all_results.items():
            if info.get('status') in ['success', 'manual_success']:
                blocks = info.get('arch_related_blocks', [])
                if blocks:
                    dependency_map[file_path] = {
                        'status': info['status'],
                        'dominant_architecture': info.get('dominant_architecture', 'unknown'),
                        'arch_related_blocks': blocks
                    }
        
        return dependency_map