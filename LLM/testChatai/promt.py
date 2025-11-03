# 1. 导入 OpenAI 聊天模型
from langchain_openai import ChatOpenAI

# 2. 导入提示词模板
from langchain_core.prompts import ChatPromptTemplate,SystemMessagePromptTemplate,HumanMessagePromptTemplate

from langchain_core.messages import HumanMessage, SystemMessage


# 3. 使用示例
llm = ChatOpenAI(
    model="deepseek-v3:671b",  # 模型名称
    openai_api_key="a21f78197ba7ada844c0479eb42459cf7be1a5cde7b57bc080e1123836654b23",
    openai_api_base="https://uni-api.cstcloud.cn/v1"

,  # 模型平台的API地址
    temperature=0.2
)

symmes = "是一个乐于助人的AI助手。"
hummes = "你好，请介绍一下你自己。"

messages = [
    SystemMessage(content=symmes), # 系统角色设定
    HumanMessage(content=hummes) # 用户消息
]
# response = llm.invoke(messages)

# print(response.content)

# 使用prompt模板重写上述示例
system_message_prompt = SystemMessagePromptTemplate.from_template(symmes)
human_message_prompt = HumanMessagePromptTemplate.from_template(hummes)
chat_prompt = ChatPromptTemplate.from_messages(
    [system_message_prompt, human_message_prompt]
)

chain = chat_prompt | llm  # 使用 | 连接

# 调用链，内部使用 invoke
response = chain.invoke({"language": "英语", "text": "你好，世界！"})
print(response.content)

# 流式调用
for s in chain.stream({"language": "英语", "text": "你好，世界！"}):
    print(s.content, end='', flush=True)

