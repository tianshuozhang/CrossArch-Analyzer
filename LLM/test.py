import os
from agents.file_utils import FileScanner
import numpy as np
from tqdm import tqdm
from langchain_openai import ChatOpenAI
from utils import setup_environment

if __name__ == "__main__":
    project_path = "LLM/config/eigen"
    setup_environment()

    llm_config = {
        "model": "deepseek-v3:671b",
        "openai_api_key": os.environ["OPENAI_API_KEY"],
        "openai_api_base": os.environ["OPENAI_API_BASE"],
        "temperature": 0.2,
    }
    llm = ChatOpenAI(**llm_config)
    # 扫描项目文件
    file_scanner = FileScanner(project_path)
    files = file_scanner.scan_all_files()
    source_files = files["source_files"]
    # 优化的prompt
    prompt = """
    你是一个资深的软件架构师，请帮助我分析以下文件路径，判断它们是否与软件架构相关。文件列表中可能有一些非架构相关的文件路径，请你仔细分析每个路径的名称和结构。大概有5%-20%的文件是架构相关的。
    返回与架构相关的文件路径，每个路径占一行。只返回文件路径，不要附加任何额外的信息，最后一行给出原本的文件列表长度与筛选出来的文件列表长度。
    这里是文件列表：
    {source_files}
    """

    # 流式调用LLM并输出结果
    response = llm.stream(
        [
            {
                "role": "user",
                "content": prompt.format(source_files="\n".join(source_files)),
            }
        ]
    )

    # response = llm.stream_usage([{"role": "user", "content": prompt.format(source_files="\n".join(source_files))}])

    print("可能的架构相关文件有：")
    for chunk in response:
        print(chunk.content, end="", flush=True)
