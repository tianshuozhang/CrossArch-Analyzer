# **面向多指令集架构的C/C++项目智能代码分类系统**

AI Agent, Flask , python, arm ,RISC-V

Description：基于大模型的智能体路线实现**自动化地识别和分类C/C++项目中对特定指令集架构的依赖代码**

## Work

### 预处理

#### Python实现一个解析C/C++预处理宏的扫描器工具（PreprocessorTool）

  Input：一段C++代码字符串

  Output：一个结构化列表，例如 [{"arch": "ARM", "start_line": 10, "end_line": 25}, ...]

实现：

1. 使用正则表达式或者一个简单的状态机来扫描代码，查找所有#if, #ifdef, #ifndef, #elif, #else, #endif。

2. 精准记录每个架构宏（如__arm__, __x86_64__, __riscv)控制的代码块的起始和结束行号。

### 提取内联汇编、编译宏、内置函数、系统调用......

#### Python实现一个提取内联汇编代码的扫描器工具（AsmQueryTool）

Output：一个结构化列表，例如 [{"line": 35, "type": "inline_asm", "content": "ldr r0, [r1]"}, ...]。

实现：使用正则表达式匹配不同风格的内联汇编，如__asm__, asm, _asm等，并提取其中的汇编代码字符串。

#### Python实现一个架构相关的内置函数(Intrinsics)的识别器工具（AsmQueryTool）

Output：一个结构化列表，例如 [{"line": 42, "type": "intrinsic", "function": "vaddq_f32", "arch": "ARM"}, ...]。

实现：

1. 预先收集一个庞大的字典或数据库，映射内置函数到其对应的架构。例如 {"_mm_add_ps": "x86_SSE", "vaddq_f32": "ARM_NEON"}。

2. 扫描代码，查找是否存在这些字典中的键（内置函数名）。

### 收集以上结果根据规则判断代码分类

设计主控制Prompt，定义任务分解和工具编排策略

1. 编写System Prompt，告诉LLM它的角色和总体目标

2. 编排工具调用：“你的任务是分析代码的架构归属。为了做到这一点，你必须先调用PreprocessorTool，然后调用AsmQueryTool。不要自己尝试阅读原始代码来找宏或汇编。

设计推理Prompt，指导LLM综合分析工具的输出

Ø "如果PreprocessorTool的结果和AsmQueryTool的结果在同一行上指向同一架构，将该行分类为______架构。"

Ø "如果PreprocessorTool的结果是'x86'，但AsmQueryTool的结果是'ARM'，你必须将该行分类为'Conflict'，并在理由中明确指出两个工具的发现。"

Ø "对于两个工具都没有报告的任何行，将其分类为'Architecture-Independent'。"

### 结果汇总并生成结构化的报告

设计输出格式Prompt，强制LLM生成可被解析的JSON报告

“你的最终回答必须是一个JSON对象，不能包含任何额外的解释性文字。该JSON对象必须包含一个名为'report'的键，其值为一个列表。列表中的每个元素都是一个对象，包含'file_path', 'line_number', 'category', 'reasoning'四个键。”（格式要求严格）

#### Python实现一个数据转换器，将LLM的报告转换为前端可视化所需格式

Output：一个专门为ECharts饼图/柱状图准备的、格式非常简单的字典。例如 {"pie_chart_data": [{"value": 1200, "name": "x86"}, {"value": 800, "name": "ARM"}, ... ]}

在Flask的API函数中编写一个【遍历上述JSON报告，统计每个架构类别的代码行数】的功能。

搭建Flask后端服务，并定义API端点

1. 创建/classifyAPI端点: 接收前端通过POST方法上传的项目压缩包（.zip）。

2. 连接【文件系统】: 编写代码来安全地处理上传的文件：保存到服务器的临时目录，然后解压缩。

3. 连接【智能体核心】: 在API函数内部调用智能体agent_executor.invoke(...)，并将解压后的代码路径作为输入。

4. 连接【数据转换器】: 接收智能体返回的JSON报告，然后调用数据转换器，生成可视化数据。

5. 连接【前端】: 将原始报告和可视化数据打包成一个大的JSON对象，通过jsonify()返回给前端。

6. 设计错误处理: 使用try...except来捕获可能发生的任何错误（如文件上传失败、解压失败、LLM API超时或返回错误格式），并向前端返回一个统一的、有意义的错误信息和HTTP状态码。

每一步调用都可以通过RAG技术来优化，即附加与查询命令语义相似度高的内容。

## Techniques

1. 下载Intel/ARM官方指令集手册、GCC/Clang内置函数文档等权威资料（PDF, HTML）。

2. 写一个Python脚本：使用LangChain的PyPDFLoader/WebBaseLoader读取文档，用RecursiveCharacterTextSplitter切块。

3. 在脚本中，使用SentenceTransformerEmbeddings将文本块向量化，然后存入一个本地的Chroma向量数据库中。

 
