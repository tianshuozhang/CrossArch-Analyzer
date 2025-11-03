from langchain_openai import ChatOpenAI

# 初始化模型，通过openai_api_base指定目标平台
model = ChatOpenAI(
    model="deepseek-v3:671b",  # 模型名称
    openai_api_key="a21f78197ba7ada844c0479eb42459cf7be1a5cde7b57bc080e1123836654b23",
    openai_api_base="https://uni-api.cstcloud.cn/v1"

,  # 模型平台的API地址
    temperature=0.2
)

# 调用模型
response = model.invoke("你好！")
print(response.content)
