from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


llm = ChatOpenAI(
    model="deepseek-v3:671b",  # 模型名称   
    openai_api_key="a21f78197ba7ada844c0479eb42459cf7be1a5cde7b57bc080e1123836654b23",
    openai_api_base="https://uni-api.cstcloud.cn/v1"
,  # 模型平台的API地址
    temperature=0.2
)

prompt = ChatPromptTemplate.from_template(
    "Tell me a short joke about {topic}"
)
output_parser = StrOutputParser()


configurable_chain = (
    {"topic": RunnablePassthrough()} 
    | prompt 
    | llm 
    | output_parser
)


for chunk in configurable_chain.stream(
    "冰淇淋", 
):
    print(chunk, end="", flush=True)
