import time
from core.Static_CodeAnalyzer import Static_CodeAnalyzer
from agents.file_utils import FileScanner, ArchitectureHeuristics
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from tqdm import tqdm
from sklearn.cluster import KMeans

if __name__ == "__main__":
    project_path = "LLM/config/eigen"
    # 扫描项目文件
    file_scanner = FileScanner(project_path)
    files = file_scanner.scan_all_files()
    source_files = files['source_files']

    pre_screened = []

    for file_path in source_files:
        is_arch, _ = ArchitectureHeuristics.is_likely_arch_related(file_path, None)
        if is_arch:
            pre_screened.append(file_path)

    files_content = file_scanner.batch_read_files(pre_screened)

    # 初始化编码模型
    embedding_model = SentenceTransformer("./LLM/models/all-MiniLM-L6-v2", device='cpu')
    # 初始化向量数据库
    dimension = embedding_model.get_sentence_embedding_dimension()

    # 初始化静态代码分析器
    analyzer = Static_CodeAnalyzer()

    high_similarity_errors = []

    # 记录总的时间
    total_start_time = time.time()

    # 初始化时间记录变量
    total_analysis_time = 0
    total_encoding_time = 0
    total_similarity_time = 0

    print("开始分析预筛选的架构相关文件...")
    
    # 如何遍历一个字典的值和键,使用tqdm显示进度条
    for file, content in tqdm(files_content.items(), desc="Analyzing files"):
        try:
            # 记录静态分析时间
            analysis_start_time = time.time()
            analysis_result, error_lines = analyzer.scan_code(content)
            analysis_end_time = time.time()
            total_analysis_time += (analysis_end_time - analysis_start_time)
        except Exception as e:
            print(f"❌ 分析文件失败 {file}: {e}")
            continue
        
        # 记录编码时间
        encoding_start_time = time.time()
        embeddings = [embedding_model.encode(file_scanner.read_file(file, line, line + 1)) for line in error_lines]
        encoding_end_time = time.time()
        total_encoding_time += (encoding_end_time - encoding_start_time)
        
        simlarity_start_time = time.time()
        # 使用 K-means 聚类来选择代表性错误行
        if len(embeddings) > 1:  # 确保至少有两个错误行
            kmeans = KMeans(n_clusters=1, random_state=0)  # 选择1个聚类中心
            kmeans.fit(embeddings)
            
            # 获取聚类中心的索引（最具代表性的错误行）
            closest_idx = np.argmin(np.linalg.norm(embeddings - kmeans.cluster_centers_, axis=1))
            representative_error_line = error_lines[closest_idx]
            
            # 存储最具代表性的错误行
            high_similarity_errors.append({
                'file': file,
                'representative_error_line': representative_error_line
            })
        else:
            # 如果只有一个错误行，直接选择
            high_similarity_errors.append({
                'file': file,
                'representative_error_line': error_lines[0]
            })
        total_similarity_time+=time.time()-simlarity_start_time

    total_end_time = time.time()
    total_time = total_end_time - total_start_time

    # 打印时间信息
    print("\n分析结束！")
    print(f"总耗时: {total_time:.2f} seconds")
    print(f"静态分析总时间: {total_analysis_time:.2f} seconds")
    print(f"编码总时间: {total_encoding_time:.2f} seconds")
    print(f"相似度计算总时间: {total_similarity_time:.2f} seconds")

    # 打印每个文件的最具代表性的错误行
    for item in high_similarity_errors:
        print(f"File: {item['file']}, Representative Error Line: {item['representative_error_line']}")
