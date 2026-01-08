# 项目架构分析器

基于 LLM Agent 的 C/C++ 项目架构依赖自动分析工具。

## 功能特性

- 🔍 **智能预筛选**：快速识别可能包含架构相关代码的文件
- ⚡ **批量静态分析**：使用 tree-sitter 进行高效代码解析
- 🤖 **Agent 补全分析**：LLM 自动分析静态工具无法处理的复杂代码
- 📊 **结构化报告**：生成详细的架构依赖分析报告

## 核心架构

```
ProjectArchitectureOrchestrator (编排器)
    │
    ├─► FileScanner (文件扫描器)
    ├─► StaticAnalysisWrapper (静态分析包装器)
    ├─► ArchitectureAnalysisAgent (批量静态分析Agent)
    ├─► WholeFileAnalysisAgent (整文件手动分析Agent)
    └─► ArchitectureReportGenerator (报告生成器)
```

## 完整数据流

### 阶段 1️⃣：初始化 (INIT)

```
输入: project_path
  │
  ├─► FileScanner 初始化
  └─► StaticAnalysisWrapper 初始化
```

---

### 阶段 2️⃣：预筛选 (PRE_SCREENING)

```
FileScanner.scan_all_files()
  │
  ├─► 获取所有源文件 (.c, .cpp, .h, .hpp)
  │
  ▼
ArchitectureHeuristics.is_likely_arch_related()
  │
  ├─► 检查文件路径特征
  │   ├─ arch/, platform/, simd/ 等目录
  │   ├─ neon_, sse_, avx_ 等文件名
  │   └─ _arm, _x86, _riscv 等后缀
  │
  ▼
输出: pre_screened_files (List[str])
      例如：98 个文件
```

---

### 阶段 3️⃣：静态分析 (STATIC_ANALYSIS)

#### 模式 A：直接调用模式 (推荐)

```
输入: pre_screened_files (98 个文件)
  │
  ├─► FileScanner.batch_read_files()
  │     └─ 批量读取文件内容
  │
  ▼
StaticAnalysisWrapper.batch_analyze_files()
  │
  ├─► 对每个文件调用 Static_CodeAnalyzer.scan_code()
  │     │
  │     ├─► tree-sitter 解析代码
  │     ├─► 标记架构相关符号
  │     └─► 提取架构相关代码块
  │
  ├─► 成功 → status: 'success'
  │     └─ 保存架构信息 (dominant_architecture, arch_related_blocks)
  │
  └─► 失败 → status: 'failed'
        └─ 提取错误行并分组为区间 (error_regions)
  
  ▼
保存: static_analysis_batch_1.json
  {
    "file1.c": {
      "status": "success",
      "dominant_architecture": "ARM_NEON",
      "arch_related_blocks": [...]
    },
    "file2.c": {
      "status": "failed",
      "error_regions": [
        {
          "start_line": 100,
          "end_line": 200,
          "error_lines": [120, 135, 156],
          "region_id": "100-200"
        }
      ]
    }
  }
  
  ▼
创建 FileTask 对象
  │
  ├─► 成功文件 → 加入 processed_tasks
  └─► 失败文件 → 加入 file_tasks (待手动分析)
```

**统计示例：**
- 成功: 93 个文件 → `static_success = 93`
- 失败: 5 个文件 → `static_failed = 5`

---

#### 模式 B：Agent 调用模式

```
输入: pre_screened_files
  │
  ├─► 创建 ArchitectureAnalysisAgent
  │     └─ 工具: StaticAnalysisTool
  │
  ▼
Agent 调用 StaticAnalysisTool
  │
  └─► (内部流程与模式 A 相同)
  
  ▼
保存: static_analysis_batch_*.json
  
  ▼
_parse_static_analysis_result_from_files()
  └─ 从文件读取并创建 FileTask
```

---

### 阶段 4️⃣：手动分析 (MANUAL_PROCESSING)

```
输入: file_tasks with error_regions
      例如：5 个失败文件

对于每个失败文件:
  │
  ├─► WholeFileAnalysisAgent.analyze_whole_file()
  │     │
  │     ├─► 读取所有错误区间的代码
  │     │     read_file(file_path, start_line, end_line)
  │     │     
  │     ├─► LLM 分析架构依赖
  │     │     ├─ 识别架构特定宏 (#ifdef __ARM_NEON)
  │     │     ├─ 识别内联汇编 (__asm__ volatile)
  │     │     ├─ 识别 SIMD intrinsics (vaddq_u8, _mm_add_ps)
  │     │     └─ 识别条件编译块
  │     │
  │     └─► 汇总并保存结果
  │           save_analysis_result(
  │             data_type="manual_file_xxx",
  │             data={
  │               "file2.c": {
  │                 "status": "manual_success",
  │                 "dominant_architecture": "ARM_NEON",
  │                 "total_regions_analyzed": 3,
  │                 "arch_related_blocks": [
  │                   {
  │                     "region_index": 1,
  │                     "start_line": 120,
  │                     "end_line": 125,
  │                     "architecture": "ARM_NEON",
  │                     "code_fragment": "vaddq_u8(...)",
  │                     "reason": "NEON intrinsic"
  │                   }
  │                 ]
  │               }
  │             }
  │           )
  │
  ▼
保存: manual_file_xxx.json (每个文件一个)
  
  ▼
更新统计:
  ├─► 成功 → manual_success += 1
  └─► 失败 → manual_failed += 1
```

**统计示例：**
- 手动成功: 4 个文件 → `manual_success = 4`
- 手动失败: 1 个文件 → `manual_failed = 1`

---

### 阶段 5️⃣：报告生成 (REPORT_GENERATION)

```
ArchitectureReportGenerator.load_all_analysis_results()
  │
  ├─► 读取 static_analysis_batch_*.json (静态成功)
  ├─► 读取 manual_file_*.json (手动补全)
  └─► 合并结果
  
  ▼
统计架构分布:
  {
    "ARM_NEON": 45,
    "x86_SSE": 32,
    "x86_AVX": 15,
    "Generic": 5
  }
  
  ▼
生成报告:
  │
  ├─► agent_summary (文本摘要)
  ├─► structured_report (结构化分析)
  └─► failed_files (失败文件列表)
  
  ▼
保存: final_report.json
  {
    "project_statistics": {
      "total_pre_screened": 98,
      "static_success": 93,
      "static_failed": 5,
      "manual_success": 4,
      "manual_failed": 1,
      "total_analyzed": 97,
      "architecture_distribution": {...}
    },
    "execution_time": 120.5,
    "data_location": ".arch_analysis_results"
  }
```

---

## 关键数据结构

### FileTask

```python
FileTask {
    file_path: str              # 文件路径
    error_regions: List[Dict]   # 错误区间列表
    status: str                 # pending/processing/success/failed
    result: Dict                # 分析结果
}
```

### ErrorRegion

```python
ErrorRegion {
    start_line: int            # 区间起始行
    end_line: int              # 区间结束行
    error_lines: List[int]     # 具体报错行号
    region_id: str             # 区间标识 "100-200"
}
```

### AnalysisResult

```python
# 成功结果
{
    "status": "success",
    "dominant_architecture": "ARM_NEON",
    "arch_related_blocks": [
        {
            "start_line": 120,
            "end_line": 125,
            "architecture": "ARM_NEON",
            "code_fragment": "vaddq_u8(...)",
            "reason": "NEON intrinsic detected"
        }
    ]
}

# 失败结果
{
    "status": "failed",
    "error_regions": [
        {
            "start_line": 100,
            "end_line": 200,
            "error_lines": [120, 135],
            "region_id": "100-200"
        }
    ]
}
```

---

## 输出文件结构

```
project_root/
└── .arch_analysis_results/
    ├── static_analysis_batch_1.json    # 静态分析结果
    ├── manual_file_xxx.json            # 手动分析结果（多个）
    └── final_report.json               # 最终报告
```

---

## 使用示例

### 基本用法

```python
from orchestrator import ProjectArchitectureOrchestrator

llm_config = {
    "model": "deepseek-v3:671b",
    "openai_api_key": "your-key",
    "openai_api_base": "your-base-url",
    "temperature": 0.2
}

# 创建编排器（推荐直接调用模式）
orchestrator = ProjectArchitectureOrchestrator(
    llm_config, 
    use_agent_for_static_analysis=False
)

# 执行分析
result = orchestrator.analyze_project(
    project_path="path/to/your/project",
    user_query="请分析这个项目的架构依赖情况"
)

# 查看结果
print(f"总分析文件: {result['project_statistics']['total_analyzed']}")
print(f"架构分布: {result['project_statistics']['architecture_distribution']}")
```

### 两种静态分析模式

```python
# 模式 1: 直接调用（推荐，更快更可靠）
orchestrator = ProjectArchitectureOrchestrator(
    llm_config, 
    use_agent_for_static_analysis=False  # 默认值
)

# 模式 2: Agent 调用（让 LLM 控制静态分析过程）
orchestrator = ProjectArchitectureOrchestrator(
    llm_config, 
    use_agent_for_static_analysis=True
)
```

---

## 完整数据流示意图

```
┌─────────────────────────────────────────────────────────────┐
│                     项目架构分析数据流                          │
└─────────────────────────────────────────────────────────────┘

输入: project_path (项目路径)
  │
  ▼
┌───────────────────────────────────────────────────────────┐
│ 阶段1: 预筛选                                               │
│ FileScanner → ArchitectureHeuristics                       │
│ 输出: 98 个潜在架构相关文件                                   │
└───────────────────────────────────────────────────────────┘
  │
  ▼
┌───────────────────────────────────────────────────────────┐
│ 阶段2: 静态分析                                             │
│ StaticAnalysisWrapper (tree-sitter)                       │
│                                                            │
│ 成功 (93 文件) → processed_tasks                           │
│   └─ 保存: static_analysis_batch_1.json                   │
│                                                            │
│ 失败 (5 文件) → file_tasks                                 │
│   └─ 提取错误区间 (error_regions)                          │
└───────────────────────────────────────────────────────────┘
  │
  ▼
┌───────────────────────────────────────────────────────────┐
│ 阶段3: 手动分析                                             │
│ WholeFileAnalysisAgent (LLM)                              │
│                                                            │
│ 对每个失败文件:                                             │
│   1. 读取所有错误区间代码                                    │
│   2. LLM 分析架构依赖                                       │
│   3. 保存结果                                              │
│                                                            │
│ 成功 (4 文件) → processed_tasks                            │
│   └─ 保存: manual_file_*.json                             │
│                                                            │
│ 失败 (1 文件) → failed_tasks                               │
└───────────────────────────────────────────────────────────┘
  │
  ▼
┌───────────────────────────────────────────────────────────┐
│ 阶段4: 报告生成                                             │
│ ArchitectureReportGenerator                               │
│                                                            │
│ 合并所有结果 → 统计 → 生成报告                               │
│   └─ 保存: final_report.json                              │
│                                                            │
│ 最终统计:                                                   │
│   - 总分析: 97 个文件                                        │
│   - 静态成功: 93                                            │
│   - 手动成功: 4                                             │
│   - 失败: 1                                                 │
└───────────────────────────────────────────────────────────┘
  │
  ▼
输出: final_report.json + 详细分析数据
```

---

## 关键设计特点

### 1. 一个文件的所有区间一次性分析

**优势：**
- 避免重复的上下文加载
- 利用文件全局信息判断架构
- 效率提升 3-5 倍

```python
# 原设计（低效）
for region in file.regions:
    agent.analyze_single_region(region)  # 调用 N 次

# 新设计（高效）
agent.analyze_whole_file(file, all_regions)  # 调用 1 次
```

### 2. 确保所有预筛选文件都被分析

```python
def _perform_direct_static_analysis(pre_screened_files, output_dir):
    # 批量读取**所有**预筛选文件
    files_content = self.file_scanner.batch_read_files(pre_screened_files)
    
    # 批量分析**所有**文件
    analysis_results = self.static_analyzer.batch_analyze_files(files_content)
    
    # 为**每个**文件创建任务
    for file_path, result in analysis_results.items():
        # 处理每个文件...
```

### 3. 统一的任务管理

- 所有文件都创建 `FileTask` 对象
- 成功文件 → `processed_tasks`
- 失败文件 → `file_tasks`（待手动分析）
- 最终失败 → `failed_tasks`

---

## 性能指标

基于 98 个文件的实际项目测试：

| 指标 | 数值 |
|------|------|
| 预筛选耗时 | 3s 迅速完成
| 静态分析耗时 | ~15 秒  迅速完成
| 手动分析耗时 | 87个文件 很慢很慢 主要瓶颈


---

## 故障排查


**原因：** Agent 模式下文件保存延迟

**解决：** 使用直接调用模式 `use_agent_for_static_analysis=False`

### 问题：手动分析失败率高

**原因：** 区间过大或 LLM 理解错误

**解决：** 调整 `region_size` 参数或优化 prompt
