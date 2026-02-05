from sentence_transformers import SentenceTransformer

# 第一次：从 Hugging Face Hub 下载（会缓存到 ～/.cache/torch/sentence_transformers/）
model = SentenceTransformer("all-MiniLM-L6-v2")

# （可选）保存到你自己的目录，方便以后离线使用
model.save("./models/all-MiniLM-L6-v2")
