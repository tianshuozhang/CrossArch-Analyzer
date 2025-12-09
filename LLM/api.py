import os
from utils import setup_environment
from agents.enhanced_orchestrator import EnhancedOrchestratorAgent
from agents.PromptParser import PromptParser
from LLM.config.config import test_all_case
setup_environment()

llm_config = {
    "model": "deepseek-v3:671b",  # 模型名称
    "openai_api_key": os.environ["OPENAI_API_KEY"],
    "openai_api_base": os.environ["OPENAI_API_BASE"],
    "temperature": 0.2
}

orchestrator = EnhancedOrchestratorAgent(llm_config, "main_orchestrator")


'''
接收前端用户输入的代码和分析需求，调用Orchestrator进行分析，并返回分析结果。用户的分析需求被分为两大类：
1. 详细分析（detailed analysis）：用户希望获得全面深入的架构依赖报告，包括代码中所有架构相关的细节。
2. 简要分析（easy analysis）：用户只需要一个高层次的概览，突出显示主要的架构依赖点，而不需要深入的细节。
文件名和代码字符串从用户上传的文件中获取。
'''
detailed_msg = "请分析以下C/C++代码文件的架构依赖情况，并提供详细的分类报告。"
easy_msg = "请简要分析以下C/C++代码文件的架构依赖情况。"

filename, code = test_all_case #一个测试用例，文件名和代码字符串

print(filename,code)

'''
如果用户输入的代码不是通过文件上传，而是直接输入在文本框和需求命令混合在一起的，则使用PromptParser进行解析，提取代码和需求命令两部分内容。
'''
# prompt_parser = PromptParser(llm_config=llm_config)
# user_prompt = "请分析以下C++代码的架构依赖：\n```cpp\n#include <iostream>\nvoid test() {\n    asm(\"mov r0, #1\");\n}\n```\n特别是其中的汇编代码，并提供重构建议。"
# code_ontent, requirements = prompt_parser.parse_promt(user_prompt)


report = orchestrator.analyze_code(code, detailed_msg, filename,"1") #report本身是一个包含详细分析结果的字典，包含多个层次的信息。

print(report["llm_enhanced_analysis"]["natural_language_report"]) #LLM的自然语言报告
print(report["llm_enhanced_analysis"]["json_data"]) #LLM的结构化JSON数据，如果是简要分析这部分是none，如果是详细分析则包含丰富的信息。


report = orchestrator.analyze(easy_msg, filename,"1")
print(report["llm_enhanced_analysis"]["natural_language_report"]) #LLM的自然语言报告
print(report["llm_enhanced_analysis"]["json_data"]) #LLM的结构化JSON数据，如果是简要分析这部分是none，如果是详细分析则包含丰富的信息。