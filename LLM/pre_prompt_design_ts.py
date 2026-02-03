from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import time

api_key = "a21f78197ba7ada844c0479eb42459cf7be1a5cde7b57bc080e1123836654b23"
api_base = "https://uni-api.cstcloud.cn/v1"

llm_config = {
    "model": "deepseek-v3:671b",  # 模型名称
    "openai_api_key": api_key,
    "openai_api_base": api_base,
    "temperature": 0.2,
}
llm = ChatOpenAI(**llm_config)

code_snippets = [
    """
EIGEN_MAKE_ARM_FP16_CMP_4(eq)
"""
]
code_snippets = "\n".join(
    ["代码片段" + str(i) + "：\n" + cs for i, cs in enumerate(code_snippets)]
)

system_prompt = """
你将收到一段 C++ 源代码，其中包含若干未定义的宏。你的任务是：仅当某处未定义宏的保留会导致标准 C++（C++17 或更新）语法解析失败时，才生成一条修复建议；否则忽略。输出应为按行号升序排列的修复方法列表，不要输出修改后的代码，也不要输出任何额外说明、标题、解释或 markdown。

请严格遵循以下规则：

1. **函数式宏调用 `NAME(...)` 的处理**：
   - 如果该调用**作为独立语句出现**（通常单独一行，或后接换行/右花括号等），且**末尾没有分号**，
     → 则它不是一个合法的 C++ 语句。
     → **建议：在该调用末尾添加分号**。
     → 输出格式：“在第 N 行的 NAME(...) 调用末尾添加分号。”
   - 如果已有分号，则视为合法表达式语句，**不要建议任何修改**。

2. **若一行仅包含一个未定义宏（无括号、无分号），且下一行是合法语句**（如 `for`, `if`, `return`, `{` 等）：
   - **建议：删除该宏**。

3. **若未定义宏出现在另一个合法语句的开头**（如 `MACRO return x;`, `MACRO int a;`）：
   - **建议：删除该宏**。

4. **若某行以未定义宏开头，后紧跟另一个标识符（或模板名），再后是变量名或函数名**（形式如 `MACRO Type name;` 或 `MACRO ReturnType func(...)`）：
   - 表明 `MACRO` 本应是 decl-specifier（如 inline、static、对齐属性等）。
   - **修复策略**：
     - 如果宏名明显对应标准关键字（如 `INLINE`→`inline`, `STATIC`→`static`, `CONSTEXPR`→`constexpr`），则替换为该关键字。
     - 否则（如 `EIGEN_ALIGN16`, `API_EXPORT`, `FORCE_INLINE` 等），**删除该宏**。

5. **输出格式**：
   - 每条建议一行，按行号升序。
   - 仅使用以下三种句式：
     - “删除第 N 行的 <宏名>。”
     - “将第 N 行的 <宏名> 替换为 <标准C++关键字>。”
     - “在第 N 行的 <宏名>(...) 调用末尾添加分号。”

注意：
- `<宏名>(...)` 是通配写法，不要展开参数，保持为 `NAME(...)` 形式。
- 不要对带分号的函数式宏做任何操作。
"""

human_prompt = f"""
请分析以下若干C++代码片段，按要求给出最小修改操作：
{code_snippets}
"""


time_start = time.time()
cnt = 1
for i in range(cnt):
    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
    )
    print(f"大模型的响应内容是：\n{response.content}")
print(f"平均花了{(time.time() - time_start)/cnt}s")
