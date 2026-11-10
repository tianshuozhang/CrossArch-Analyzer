<div align="center">

# 🧬 CrossArch-Analyzer

**LLM agents + static analysis for cross-architecture (x86 / ARM / RISC-V) C/C++ code**
**大模型 Agent + 静态分析的跨架构 C/C++ 代码分析与修复**

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![C++](https://img.shields.io/badge/C++-00599C?style=flat-square&logo=cplusplus&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)
![tree-sitter](https://img.shields.io/badge/tree--sitter-2E7D32?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)

</div>

---

## 📖 Overview · 简介

**English** — The tool finds architecture-specific code (SIMD intrinsics, `arch/` and platform macros, etc.) in large C/C++ projects such as Eigen. It uses **tree-sitter static analysis** for the bulk of the work and calls **LLM agents** only for ambiguous regions. Errors found by the static analyser are clustered (sentence embeddings + K-means), so the LLM repairs only representative lines. This cuts token cost substantially.

**中文** — 面向 Eigen 等大型 C/C++ 项目，自动识别与体系结构相关的代码（SIMD 指令、`arch/` 目录、平台宏等）。主体工作由 **tree-sitter 静态分析** 完成，只有模糊的部分才交给 **LLM Agent**。静态分析发现的错误行先做聚类（句向量 + K-means），大模型只修复其中有代表性的行，从而大幅降低 Token 开销。

## 🗂️ Components · 模块

| Path · 路径 | Description · 说明 |
| --- | --- |
| [`LLM/`](LLM/) | Analyzer core: pre-screening, static analysis, agents, report generation ([details](LLM/README.md)) · 分析器核心 |
| `code-annotation-backend-master/` | Flask backend serving the analysis API · Flask 后端 |
| `code-annotation-frontend/` | Web front-end for browsing annotations · 前端标注界面 |
| `run.sh` / `run.bat` | One-click launch scripts · 一键启动脚本 |

```text
Pre-screening ─► Static analysis (tree-sitter) ─► LLM agent completion ─► Architecture report
  预筛选              批量静态分析                      Agent 补全分析               结构化报告
```

---

### 项目流程概述

该项目的目标是通过静态分析和大语言模型（LLM）的协作，逐步修复代码中的错误。在这个流程中，首先执行静态代码分析来检测错误，然后根据分析结果选择较为普遍的错误类型，再通过大模型进行针对性的修复。这个过程会重复进行，直到静态分析结果显示错误已经得到显著修复为止。

### 流程的主要步骤：

1. **静态分析阶段**：

   * 执行静态分析，识别代码中的错误（语法错误、代码质量问题等）。
   * 将这些错误行提取出来，进一步分类并分析。

2. **错误筛选和聚类**：

   * 根据静态分析的结果，筛选出较为普遍的错误类型。
   * 使用聚类方法（如 K-means）对错误行进行分类，选出最具代表性的错误行。这里的代表性错误行指的是那些频繁出现、具有较高修复价值的错误行，而非每个文件中的所有错误行。

3. **大模型修复**：

   * 使用大模型来修复这些选出的代表性错误行。
   * 每次修复后的代码会被返回，并重新进行静态分析，检查修复是否有效。

4. **迭代修复**：

   * 在每次修复之后，系统会重新执行静态分析，检查错误是否已经减少。如果错误仍然存在，继续进行下一轮修复，直到错误数显著减少，或者达到了预设的停止条件。

5. **最终结果输出**：

   * 在完成修复后，输出最终的修复报告，包括已修复的错误行、修复的时间以及每个阶段的处理结果。

---

### 详细流程：静态分析出错部分筛选和修复
完整代码在LLM/api.py，这里最大化复用了此前使用的各种工具。

#### 1. **静态分析与错误检测**

首先，程序使用静态分析工具（如 `Static_CodeAnalyzer`）对项目中的代码进行分析。静态分析能够找出潜在的错误行，包括：

* 语法错误
* 代码质量问题（例如复杂度过高的函数、重复代码、缺乏注释等）
* 安全问题
* 潜在的 bug

```python
analysis_result, error_lines = analyzer.scan_code(content)
```

在静态分析阶段，所有错误行会被捕获并返回。此时，这些错误是没有经过筛选的，包括每个文件中所有的错误行。

#### 2. **筛选和聚类：选择代表性错误行**

接下来，使用聚类算法（如 K-means）筛选出最具代表性的错误行，而不是直接修复每个错误行。筛选步骤是基于以下几个目标：

* **聚焦于重复的错误**：大多数错误行在不同文件或不同部分可能是重复的，修复这些错误通常会带来更大的改进效果。
* **优先修复高频错误**：一些常见的错误（如重复的变量声明、常见的命名错误等）对代码质量的提升作用更大，应该优先修复。

```python
# 使用 K-means 聚类来选择代表性错误行
if len(embeddings) > 1:  # 确保至少有两个错误行
    kmeans = KMeans(n_clusters=1, random_state=0)  # 选择1个聚类中心
    kmeans.fit(embeddings)
    
    # 获取聚类中心的索引（最具代表性的错误行）
    closest_idx = np.argmin(np.linalg.norm(embeddings - kmeans.cluster_centers_, axis=1))
    representative_error_line = error_lines[closest_idx]
    
    # 存储最具代表性的错误行
    high_similarity_errors.append({
        'file': file,
        'representative_error_line': representative_error_line
    })
```

通过这种方式，程序会将错误行进行聚类，选出那些具有代表性、修复价值较高的错误行，避免一次性修复所有错误，这样可以有效节省大模型的计算资源。

#### 3. **大模型修复**

修复过程由LLM完成。模型会对选中的代表性错误行进行修复。每次修复后，模型会返回一个修复版本的代码。

```python
# 使用大模型修复代表性错误行
修复后的代码 = large_model.fix_code(代表性错误行)
```

#### 4. **重新静态分析与迭代**

每次修复后，程序会重新对修复后的代码进行静态分析，检查修复是否成功。如果修复有效（即错误减少），继续下一轮修复。否则，再次执行错误筛选和修复流程。

```python
# 重新执行静态分析，检查修复效果
analysis_result, error_lines = analyzer.scan_code(修复后的代码)
```

这个步骤会不断重复，直到静态分析的结果没有错误，或者错误数降到可以接受的程度。


### 为什么筛选错误行比直接修改代码更高效

1. **节省计算资源（Tokens 消耗）**：

   * 大语言模型通常是按 **输入文本的 Token 数量**计费的。直接修复每一行错误需要将每个错误行的上下文传递给模型，这会消耗大量的 Token，尤其是当代码中有成百上千行错误时。
   * 通过先筛选出代表性错误行（最频繁和最具影响力的错误），只修复这些错误行，可以大大减少每次调用大模型时所需的 Token 数量。

2. **提高修复效率**：

   * 聚类方法帮助我们集中精力解决那些对代码质量改进最有价值的问题。选择代表性错误行而不是逐个处理每个错误，可以更有效地提升代码的整体质量。

3. **避免重复修复**：

   * 大多数代码中的错误是相似或重复的。通过聚类，模型可以集中修复这些重复错误，而不是重复修复每个文件中的相同问题。这不仅提高了修复的速度，还降低了 Token 消耗。


### 时间消耗分析
对于Eigen科学计算库，通过预筛选后的文件（98）进行一轮静态分析，错误的编码聚类，时间消耗大致如下：
总耗时: 59.74 seconds
静态分析总时间: 2.15 seconds
编码总时间: 55.05 seconds
每条错误行平均编码时间: 0.01 seconds
相似度计算总时间: 0.31 seconds


### 总结

通过筛选出最具代表性的错误行，并集中修复这些错误，我们能够：

* **显著减少大语言模型的计算资源消耗**，因为只修复少量的代表性错误行而非每个错误行。
* **提高代码修复效率**，避免重复修复相同的错误。
* **节省时间和提高准确性**，通过聚类和筛选，集中精力解决最影响架构和质量的问题。

这一流程比直接让大模型修复所有错误行更加高效，尤其是在大规模代码库和高并发场景下，能够显著减少计算资源的消耗。

