import json
from typing import Tuple, Dict, Any
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
class PromptParser:
    # 假设 self.llm 是您用于调用大模型的接口
    # 为了演示，这里定义为 None，您需要根据您的 LLM 库（如 LangChain 或 OpenAI）进行初始化
    def __init__(self, llm_config: Any):
        self.llm = ChatOpenAI(**llm_config)
    def parse_promt(self, prompt: str) -> Tuple[str, str]:
        """
        解析用户的提示词，通过 LLM 提取其中的代码块和需求描述，
        并返回 (code_content, requirements_description) 元组。
        """
        
        # 1. 构建 System Message 和 Human Message
        system_message = self._build_system_message()
        human_message = self._build_human_message(prompt)

        chat_prompt = ChatPromptTemplate.from_messages(
        [SystemMessage(content=system_message), HumanMessage(content=human_message)]
        )
        chain = chat_prompt|self.llm
        
        # 3. 调用 LLM 进行解析
        # 假设 self.llm_chain.invoke(llm_input) 返回包含 JSON 字符串的响应对象
        try:
            llm_response = chain.invoke({})
            
            # LLM 的输出内容，通常在 .content 或类似的属性中
            llm_output = llm_response.content 
            
            # 4. 解析 JSON 输出
            parsed_data = self._parse_llm_json_output(llm_output)

            # 5. 返回元组
            return parsed_data.get("code", ""), parsed_data.get("requirements", "")
            
        except Exception as e:
            print(f"Error during LLM parsing: {e}")
            # 解析失败时，将整个 prompt 视为需求，代码为空
            return "", f"无法解析内容，原始提示词：{prompt}"

    def _build_system_message(self) -> str:
        """定义 LLM 的角色和输出格式约束。"""
        return """
        你是一个专业的文本解析助手。你的任务是将用户提供的提示词精确地分割成两个部分：
        1. 完整且未经修改的代码内容（code）。
        2. 对该代码的分析或修改需求（requirements）。

        请严格遵循以下规则：
        - 识别并提取所有被 Markdown 符号 (```) 包裹的代码块，作为 'code' 的值。如果存在多个代码块，请将它们合并。
        - 剩余的所有自然语言文本、说明、指令或上下文，作为 'requirements' 的值。
        - 即使没有找到代码块，也必须返回 'code' 键，其值为空字符串。
        - 你的最终输出必须是一个可解析的 JSON 对象，不能包含任何额外的文本或解释。
        """
    
    def _build_human_message(self, prompt: str) -> str:
        """构建包含实际输入数据的用户消息。"""
        current_time = datetime.now().isoformat()
        return f"""
        请解析以下用户输入的提示词。确保将所有代码内容和所有非代码内容（需求）准确分离。

        --- 解析上下文 ---
        分析时间: {current_time}
        
        --- 用户提示词 ---
        {prompt}
        """

    def _parse_llm_json_output(self, llm_output: str) -> Dict[str, str]:
        """从 LLM 输出中提取并解析 JSON 字符串。"""
        # 使用正则表达式或字符串查找来定位最外层的 JSON 块
        try:
            # 寻找最外层的 {}
            start = llm_output.find("{")
            end = llm_output.rfind("}")
            
            if start != -1 and end != -1 and start < end:
                json_str = llm_output[start : end + 1]
                return json.loads(json_str)
        except Exception as e:
            print(f"JSON解析失败: {e}")
            
        # 如果解析失败，返回默认结构
        return {"code": "", "requirements": llm_output}

# --- 示例调用（需要替换 self.llm_chain 部分） ---
if __name__ == "__main__":

    llm_config = {
        "model": "deepseek-v3:671b",  # 模型名称
        "openai_api_key": "a21f78197ba7ada844c0479eb42459cf7be1a5cde7b57bc080e1123836654b23",
        "openai_api_base": "https://uni-api.cstcloud.cn/v1",
        "temperature": 0.2
    }
    parser = PromptParser(llm_config=llm_config)
    
    # 示例输入
    user_prompt = "请分析以下C++代码的架构依赖：\n```cpp\n#include <iostream>\nvoid test() {\n    asm(\"mov r0, #1\");\n}\n```\n特别是其中的汇编代码，并提供重构建议。"
    
    code_content, requirements = parser.parse_promt(user_prompt)
    
    print("\n--- 解析结果 ---")
    print(f"代码内容:\n{code_content}")
    print("-" * 20)
    print(f"需求描述: {requirements}")