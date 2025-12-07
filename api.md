# 后端调用Agent的使用说明

通过LLM目录下的**api.py**进行调用，下面给出两个数据结构PromptParser和OrchestratorAgent的使用说明。

-----

## 1\. 用户输入解析接口 (`PromptParser`)

该接口用于处理用户将**代码**和**需求**混合输入到同一个文本框的场景。

### `PromptParser.parse_promt`

**功能：** 通过 LLM 解析原始用户输入，将其中的代码块和需求描述分离。

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `prompt` | `str` | 包含代码（通常由 ` ``` ` 包裹）和分析需求描述的原始用户输入字符串。 |

**返回值：** `Tuple[str, str]`

  * **返回值 1 (`str`)：** 提取出的完整代码内容（`code_content`）。如果未找到代码，则返回空字符串 `""`。
  * **返回值 2 (`str`)：** 提取出的用户需求描述（`requirements`）。

**使用示例：**

```python
# 初始化时需要 LLM 配置
prompt_parser = PromptParser(llm_config=llm_config) 
code_content, requirements = prompt_parser.parse_promt(user_prompt)
```

-----

## 2\. 代码静态分析接口 (`OrchestratorAgent`)

该接口用于调用核心分析逻辑。实现了两种分析场景：提供代码进行分析，或基于已知的代码和元数据进行分析。

### 接口概览

| 函数名 | 场景 | 必传参数 |
| :--- | :--- | :--- |
| `analyze_code` | **代码直传**：用户输入代码和需求，需要立即执行分析。 | `code`, `msg`, `filename` |
| `analyze` | **代码已就绪**：代码已通过文件上传或先前步骤处理，只需提供分析需求和元数据。 | `msg`, `filename`|

### `OrchestratorAgent.analyze_code` (包含代码的分析)

**功能：** 接收代码、分析需求、文件名和会话 ID，执行完整的**静态分析 -\> 体系结构标记 -\> LLM 增强报告**流程。

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `code` | `str` | **待分析的完整代码字符串。** |
| `msg` | `str` | 用户分析需求（如 `detailed_msg` 或 `easy_msg`），决定 LLM 的输出模式（JSON/简要）。 |
| `filename` | `str` | 待分析的文件名，用于元数据报告。 |
| `session_id` | `str` | 当前会话的唯一标识符。 |

**使用示例：**

```python
report = orchestrator.analyze_code(code, easy_msg, filename, "1")
```

### `OrchestratorAgent.analyze` (不包含代码的分析)

**功能：** **（假设）** 仅基于提供的分析需求和元数据生成报告。适用于代码内容已在 orchestrator 内部或上一步骤中缓存/处理的场景。

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `msg` | `str` | 用户分析需求（如 `detailed_msg`），决定 LLM 的输出模式（JSON/简要）。 |
| `filename` | `str` | 报告所基于的文件名。 |
| `session_id` | `str` | 当前会话的唯一标识符。 |

**使用示例：**

```python
report = orchestrator.analyze(detailed_msg, filename, "1")
```

-----

## 3\. 报告结果解析

两个分析函数（`analyze_code` 和 `analyze`）都返回一个包含 LLM 增强分析结果的字典。

| 键 | 内容 | 说明 |
| :--- | :--- | :--- |
| `report["llm_enhanced_analysis"]["natural_language_report"]` | `str` | LLM 生成的自然语言报告，无论简要还是详细模式，都包含此部分。 |
| `report["llm_enhanced_analysis"]["json_data"]` | `dict` 或 `None` | LLM 生成的结构化 JSON 数据。**简要分析时为 `None`**；**详细分析时包含完整的结构化报告。** |