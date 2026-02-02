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
        return response.content

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
        def _cal_score(args):
            error_vector_dict, content, history_data = args
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
        if len(self.history_data) > 10:
            return False
        if len(self.history_data) > 2 and self.history_data[-2] - self.history_data[-1] < 3:
            return False
        if self.history_data[-1] < 10:
            return False
        return True

    def rankTopXErrors(
        self, error_vector_dict: dict[ErrorSnippet, VectorType]
    ) -> list[ErrorSnippet]:
        # TODO:根据向量按照Kmeans计算，选出得分最高的前X个错误
        embeddings = np.array([vector for vector in error_vector_dict.values()])
        n_clusters = min(1, len(embeddings))  # 确保聚类数不超过样本数
        if len(embeddings) > n_clusters:  # 确保至少有两个错误行
            kmeans = KMeans(n_clusters=n_clusters, random_state=0)  # 选择1个聚类中心
            kmeans.fit(embeddings)
            representative_error_snippet = []
            for cluster_center in kmeans.cluster_centers_:
                distances = np.linalg.norm(embeddings - cluster_center, axis=1)
                closest_idx = np.argmin(distances)  # 找到距离最小的样本
                representative_error_snippet.append(list(error_vector_dict.keys())[closest_idx])
                
        else:
            representative_error_snippet = list(error_vector_dict.keys())
        return representative_error_snippet

    def getLLMadvice(self, errors: list[ErrorSnippet])-> list[ModifyPattern]:
        # TODO:将errors包装成user_prompt，然后交给大模型得到建议（如果一次请求时间太长就重新请求）？
        # 检查建议内容格式正确后返回防止幻觉，否则再重复调几次，如果一直失败就给个默认建议？
        # 默认建议可以是不修改
        def _checkLLMadvice(response_content: str):
            # TODO：检查大模型有没有出现幻觉
            return True or False
        user_prompt = "请根据以下代码片段，生成修改建议：\\n\\n"
        for error in errors:
            user_prompt += f"代码片段：\n{error.code_content}\\n\\n"
        response = self.agent.get_response(user_prompt)
        # TODO:解析response为ModifyPattern对象列表
        pattern = r"<(.*?)> 替换为 <(.*?)>"
        matches = re.findall(pattern, response)
        modify_patterns = [ModifyPattern(before_pattern=f"<{match[0]}>", after_pattern=f"<{match[1]}>") for match in matches]
        return modify_patterns  

    @staticmethod
    def getFallbackAdvice(errors: list[ErrorSnippet]):
        # TODO:fallback的处理就是直接删除errors的代码片段？即我们放弃对这些片段的架构分类标注
        return [ModifyPattern(before_pattern=error.code_content, after_pattern='<null>') for error in errors]

    @staticmethod
    def rewriteContent(
        args,
        content: str = None,
        errors: list[ErrorSnippet] = None,
        advice: list[ModifyPattern] = None,
    ) -> tuple[str, list[DepRelation]]:
        # TODO:对于每个错误看看是否可以匹配建议，如果匹配的话，先生成一条tagTarget_relation，然后修改content的内容
        # WARNING: 修改content的时候**不能改变error原本的行数**，例如不能5行变4行，
        # 因为之后还要对这个content用ts分析，如果行号变了，那么就是不同的tag_target了
        content,errors,advice = args        
        tagTarget_relations = []
        # 遍历所有修改建议
        for suggestion in advice:
            before_pattern = re.escape(suggestion.before_pattern)  # 将特殊字符转义
            after_pattern = re.escape(suggestion.after_pattern)  # 将特殊字符转义
            if after_pattern == "<null>":
                # 跨行匹配
                multi_line_pattern = re.compile(before_pattern, re.DOTALL)  # DOTALL 允许'.'匹配换行符
                
                # 查找所有匹配的跨行代码块
                matches = multi_line_pattern.finditer(content)
                for match in matches:
                    # 在跨行代码块的地方，用空白行替换掉，确保行数不变
                    matched_text = content[match.start():match.end()]
                    matched_lines = matched_text.splitlines()
                    
                    # 生成等长的空白行，确保删除的行数与原始行数一致
                    replacement_lines = [' ' * len(line) for line in matched_lines]
                    replacement_text = "\n".join(replacement_lines)
                    
                    # 替换掉代码块，保持原来的行数
                    content = content[:match.start()] + replacement_text + content[match.end():]
                    
                    # 记录标签关系
                    tagTarget_relations.append(DepRelation(match, suggestion))
            # 对content进行正则匹配和替换
            else:
                new_content = []
                for line in content.splitlines():
                    match = re.search(before_pattern, line)
                    if match:
                        # 找到匹配内容，进行替换
                        modified_line = re.sub(before_pattern, after_pattern, line)
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
        embedding_model = SentenceTransformer("./LLM/models/all-MiniLM-L6-v2", device='cpu')
        embeddings = {error_snippet:embedding_model.encode(error_snippet.code_content) for error_snippet in errors[0]}
        return embeddings

    @staticmethod
    def rewrite(
        file_paths: list[str],
        _,
        file_errors: FileResultDict[list[ErrorSnippet]],
    ) -> FileResultDict[list[DepRelation]]:
        def _read_file(p):
            with open(p[0], "r") as f:
                return f.read()

        def _write_file(args):
            p, content = args
            with open(p, "w") as f:
                f.write(content)

        code_rewritter = CodeRewriter()
        file_content = ph.map(file_paths, _read_file, use_path=True)
        file_error_vector_dicts: FileResultDict[dict[ErrorSnippet, VectorType]] = (
            ph.map(file_paths, CodeRewriter.vectorize, file_errors)
        )
        errors = ph.de_file_and_merge(file_errors)
        # file_tagTarget_relations_total = ph.map(file_paths, lambda: [])
        file_tagTarget_relations_total = ph.map(file_paths, lambda file_path: [])
        while len(errors) > 0:
            print(f"当前还有 {len(errors)} 处错误需要重写...")
            code_rewritter.recordHistory(errors)
            useLLM = code_rewritter.choose_llm_or_fallback(
                file_paths, file_error_vector_dicts, file_content
            )
            print(f"本轮重写使用 {'LLM' if useLLM else 'Fallback'} 策略")
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
            def _merge_tagTarget_relations(args):
                total, new = args
                return total + new
            file_tagTarget_relations_total = ph.map(
                file_paths,
                _merge_tagTarget_relations,
                file_tagTarget_relations_total,
                file_tagTarget_relations,
            )
            _, file_errors = ph.map_out_tuple(file_paths, sct.scan_code, file_content)
            errors = ph.de_file_and_merge(file_errors)
            def filter_errors_by_vector(args,error_vector_dict: dict[ErrorSnippet, VectorType] = None, 
                                        errors: list[ErrorSnippet]= None,
                ) -> dict[ErrorSnippet, VectorType]:
                error_vector_dict, errors = args
                return {
                    error: vector
                    for error, vector in error_vector_dict.items()  # 使用 .items() 来遍历字典
                    if error in errors  # 只保留在 errors 列表中的错误
                }

            file_error_vector_dicts = ph.map(
                file_paths,
                filter_errors_by_vector,
                file_error_vector_dicts,
                file_errors,
            )

        ph.map(file_paths, _write_file, file_content, use_path=True)

        return file_tagTarget_relations_total
