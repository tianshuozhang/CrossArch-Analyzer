import utils.static_classify_tool as sct
from utils.llm_prompts import system_prompts_for_codeRewriter
from utils.data_structures import *
import utils.project_helper as ph
from module.code_analyzer import CodeAnalyzer
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import numpy as np
import re
from langchain_openai import ChatOpenAI
import os
class Agent:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        
        llm_config = {
            "model": "deepseek-v3:671b",  # 模型名称
            "openai_api_key": "a21f78197ba7ada844c0479eb42459cf7be1a5cde7b57bc080e1123836654b23",
            "openai_api_base": "https://uni-api.cstcloud.cn/v1",
            "temperature": 0.2
        }
        self.llm = ChatOpenAI(**llm_config)
    def get_response(self, user_prompt: str) -> str:
        response = self.llm.invoke([
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        return response['choices'][0]['message']['content']

class CodeRewriter:
    def __init__(self):
        self.history_data = []
        self.agent = Agent(system_prompts_for_codeRewriter)

    def recordHistory(self, errors: list[ErrorSnippet]):
        # TODO:现在先简单地只记录错误数？
        self.history_data.append(len(errors))

    def choose_llm_or_fallback(
        self,
        file_paths: list[str],
        file_error_vector_dict: FileResultDict[dict[ErrorSnippet, VectorType]],
        file_content: FileResultDict[str],
    ):
        # TODO:根据self.history_data、file_error_vector_dict、file_content评估该用哪个？
        def _cal_score(error_vector_dict, content, history_data):
            return

        scores = ph.de_file_and_merge(
            ph.map(
                file_paths,
                _cal_score,
                file_error_vector_dict,
                file_content,
                self.history_data,
            )
        )

        return True or False

    def rankTopXErrors(
        self, error_vector_dict: dict[ErrorSnippet, VectorType]
    ) -> list[ErrorSnippet]:
        # TODO:根据向量按照Kmeans计算，选出得分最高的前X个错误
        embedding_model = SentenceTransformer("./LLM/models/all-MiniLM-L6-v2", device='cuda')
        embeddings = [embedding_model.encode(error_snippet.code_content) for error_snippet in error_vector_dict.keys()]
        # 使用 K-means 聚类来选择代表性错误行
        if len(embeddings) > 3:  # 确保至少有两个错误行
            kmeans = KMeans(n_clusters=3, random_state=0)  # 选择1个聚类中心
            kmeans.fit(embeddings)
            
            # 获取聚类中心的索引（最具代表性的错误行）
            closest_idx = np.argmin(np.linalg.norm(embeddings - kmeans.cluster_centers_, axis=1))
            #取出error_vector_dict字典中对应的ErrorSnippet
            representative_error_snippet = list(error_vector_dict.keys())[closest_idx]
            
        else:
            representative_error_snippet = list(error_vector_dict.keys())
        return representative_error_snippet

    def getLLMadvice(self, errors: list[ErrorSnippet]):
        # TODO:将errors包装成user_prompt，然后交给大模型得到建议（如果一次请求时间太长就重新请求）？
        # 检查建议内容格式正确后返回防止幻觉，否则再重复调几次，如果一直失败就给个默认建议？
        # 默认建议可以是不修改
        def _checkLLMadvice(response_content: str):
            # TODO：检查大模型有没有出现幻觉
            return True or False
        user_prompt = "请根据以下代码片段，生成修改建议：\n\n"
        for error in errors:
            user_prompt += f"代码片段：\n{error.code_content}\n\n"
        response = self.agent.get_response(user_prompt)
        print("LLM response:", response)
        # TODO:解析response为ModifyPattern对象列表  
        
        return [ModifyPattern]

    @staticmethod
    def getFallbackAdvice(errors: list[ErrorSnippet]):
        # TODO:fallback的处理就是直接删除errors的代码片段？即我们放弃对这些片段的架构分类标注
        return [ModifyPattern]

    @staticmethod
    def rewriteContent(
        content: str,
        errors: list[ErrorSnippet],
        advice: list[ModifyPattern],
    ) -> tuple[str, list[DepRelation]]:
        # TODO:对于每个错误看看是否可以匹配建议，如果匹配的话，先生成一条tagTarget_relation，然后修改content的内容
        # WARNING: 修改content的时候**不能改变error原本的行数**，例如不能5行变4行，
        # 因为之后还要对这个content用ts分析，如果行号变了，那么就是不同的tag_target了        
        tagTarget_relations = []
        # 遍历所有修改建议
        for suggestion in advice:
            before_pattern = suggestion.before_pattern
            after_pattern = suggestion.after_pattern
            # 对content进行正则匹配和替换
            new_content = []
            for line in content.splitlines():
                match = re.search(before_pattern, line)
                if match:
                    # 找到匹配内容，进行替换
                    modified_line = re.sub(before_pattern, after_pattern, line)
                    
                    # 保持行数不变，填充空格
                    if len(modified_line) < len(line):
                        # 填充空格保持长度不变
                        modified_line = modified_line + ' ' * (len(line) - len(modified_line))
                    elif len(modified_line) > len(line):
                        # 如果修改后的内容过长，进行截断
                        modified_line = modified_line[:len(line)]
                    # 记录标签关系 (可以根据需要进行扩展)
                    tagTarget_relations.append(DepRelation(match, suggestion))
                    new_content.append(modified_line)
                else:
                    # 如果没有匹配到，就保留原始行
                    new_content.append(line)
            # 将修改后的内容拼接成新的字符串
            content = "\n".join(new_content)
        return content, tagTarget_relations

    @staticmethod
    def vectorize(errors: list[ErrorSnippet]) -> dict[ErrorSnippet, VectorType]:
        # TODO:计算errors的向量，返回<error,vector>的字典，VectorType的类型定义在utils/data_structures修改
        return

    @staticmethod
    def rewrite(
        file_paths: list[str],
        _,
        file_errors: FileResultDict[list[ErrorSnippet]],
    ) -> FileResultDict[list[DepRelation]]:
        def _read_file(p):
            with open(p, "r") as f:
                return f.read()

        def _write_file(p, content):
            with open(p, "w") as f:
                f.write(content)

        code_rewritter = CodeRewriter()
        file_content = ph.map(file_paths, _read_file, use_path=True)
        file_error_vector_dicts: FileResultDict[dict[ErrorSnippet, VectorType]] = (
            ph.map(file_paths, CodeRewriter.vectorize, file_errors)
        )
        errors = ph.de_file_and_merge(file_errors)
        file_tagTarget_relations_total = ph.map(file_paths, lambda: [])
        while len(errors) > 0:
            code_rewritter.recordHistory(errors)
            useLLM = code_rewritter.choose_llm_or_fallback(
                file_paths, file_error_vector_dicts, file_content
            )
            if useLLM:
                selected_errors = code_rewritter.rankTopXErrors(
                    ph.de_file_and_merge(file_error_vector_dicts)
                )
                advice = code_rewritter.getLLMadvice(selected_errors)
                print(advice)
            else:
                advice = CodeRewriter.getFallbackAdvice(errors)
            file_content, file_tagTarget_relations = ph.map_out_tuple(
                file_paths,
                CodeRewriter.rewriteContent,
                file_content,
                file_errors,
                advice,
            )
            file_tagTarget_relations_total = ph.map(
                file_paths,
                lambda total, new: total + new,
                file_tagTarget_relations_total,
                file_tagTarget_relations,
            )
            _, file_errors = ph.map_out_tuple(file_paths, sct.scan_code, file_content)
            errors = ph.de_file_and_merge(file_errors)
            file_error_vector_dicts = ph.map(
                file_paths,
                lambda error_vector_dict, errors: {
                    error: vector
                    for error, vector in error_vector_dict
                    if error in errors
                },
                file_error_vector_dicts,
                file_errors,
            )

        ph.map(file_paths, _write_file, file_content, use_path=True)

        return file_tagTarget_relations_total
