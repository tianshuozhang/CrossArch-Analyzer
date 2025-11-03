import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import faiss

@dataclass
class MemoryItem:
    """记忆项数据结构"""
    content: str
    timestamp: datetime
    importance: float  # 重要性评分 (0-1)
    memory_type: str   # "conversation", "analysis_result", "rule_pattern"
    metadata: Dict[str, Any]

class MemoryManager:
    """记忆管理器：基于RAG的记忆检索和总结"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # 初始化文本嵌入模型
        self.embedding_model = SentenceTransformer(model_name)
        
        # 创建FAISS向量索引
        self.vector_dim = 384  # all-MiniLM-L6-v2的维度
        self.index = faiss.IndexFlatIP(self.vector_dim)  # 内积相似度
        
        # 记忆存储
        self.memories: List[MemoryItem] = []
        self.memory_vectors = np.empty((0, self.vector_dim))
        
    def add_memory(self, content: str, memory_type: str = "conversation", 
              importance: float = 0.5, metadata: Optional[Dict] = None):
        """添加新的记忆项（优化版本）"""
        memory_item = MemoryItem(
            content=content,
            timestamp=datetime.now(),
            importance=importance,
            memory_type=memory_type,
            metadata=metadata or {}
        )
        
        # 生成向量嵌入
        embedding = self.embedding_model.encode([content])
        vector = embedding.astype('float32')
        
        # 添加到存储
        self.memories.append(memory_item)
        
        # 添加到向量集合
        if len(self.memory_vectors) == 0:
            self.memory_vectors = vector
        else:
            self.memory_vectors = np.vstack([self.memory_vectors, vector])
        
        # 优化索引重建：只在必要时重建
        if hasattr(self, 'index'):
            # 增量添加向量到现有索引
            self.index.add(vector)
        else:
            # 首次创建索引
            self.index = faiss.IndexFlatIP(self.vector_dim)
            self.index.add(self.memory_vectors)

    
    def retrieve_relevant_memories(self, query: str, top_k: int = 5, 
                                  memory_type: Optional[str] = None) -> List[MemoryItem]:
        """基于RAG检索相关记忆"""
        # 生成查询向量
        # 检查索引是否为空
        if len(self.memories) == 0:
            print("记忆库为空，无法检索")
            return []
        
        if self.index.ntotal == 0:
            print("FAISS索引为空，但记忆库有内容，需要重建索引")
            self._rebuild_index()

        query_embedding = self.embedding_model.encode([query])
        query_vector = query_embedding.astype('float32')
        
        # 相似度搜索 - 确保返回足够的结果用于后续过滤
        search_k = min(top_k * 3,len(self.memories))  # 多返回一些结果用于过滤
        similarities, indices = self.index.search(query_vector, search_k)
        
        
        # 相似度搜索
        
        # 过滤和排序结果
        results = []
        valid_indices = indices[0]
        similarities_list = similarities[0]
        for i, idx in enumerate(valid_indices):
            # 检查索引是否有效（非负且不越界）
            if idx >= 0 and idx < len(self.memories):
                memory = self.memories[idx]
                similarity_score = similarities_list[i]  # 获取对应的相似度分数
                
                # 类型过滤
                if memory_type is None or memory.memory_type == memory_type:
                    results.append({
                        'memory': memory,
                        'similarity': similarity_score,
                        'score': similarity_score * memory.importance  # 综合评分
                    })
            else:
                print(f"跳过无效索引: {idx}")
        
        # 按综合评分排序并返回top_k
        results.sort(key=lambda x: x['score'], reverse=True)

        return [r['memory'] for r in results[:top_k]]
    
    def summarize_memories(self, max_tokens: int = 1000) -> str:
        """记忆递归总结：将大量记忆压缩为简洁摘要"""
        if not self.memories:
            return "暂无记忆"
        
        # 按重要性排序
        important_memories = sorted(self.memories, 
                                  key=lambda x: x.importance, reverse=True)
        
        summary_parts = []
        current_length = 0
        
        for memory in important_memories:
            memory_text = f"[{memory.memory_type}] {memory.content}"
            
            if current_length + len(memory_text) <= max_tokens:
                summary_parts.append(memory_text)
                current_length += len(memory_text)
            else:
                break
        
        return "\n".join(summary_parts) if summary_parts else "记忆摘要为空"
    
    def cleanup_old_memories(self, max_count: int = 1000):
        """清理旧记忆，控制内存使用"""
        if len(self.memories) > max_count:
            # 按重要性保留最重要的记忆
            self.memories.sort(key=lambda x: x.importance, reverse=True)
            self.memories = self.memories[:max_count]
            
            # 重新构建向量索引
            self.memory_vectors = np.empty((0, self.vector_dim))
            for memory in self.memories:
                embedding = self.embedding_model.encode([memory.content])
                vector = embedding.astype('float32')
                self.memory_vectors = np.vstack([self.memory_vectors, vector])
            
            self.index = faiss.IndexFlatIP(self.vector_dim)
            self.index.add(self.memory_vectors)
    def _rebuild_index(self):
        """重建FAISS索引"""
        if len(self.memory_vectors) > 0:
            self.index = faiss.IndexFlatIP(self.vector_dim)
            # 添加前归一化向量（用于余弦相似度）
            normalized_vectors = self.memory_vectors.copy()
            faiss.normalize_L2(normalized_vectors)
            self.index.add(normalized_vectors)
            print(f"索引重建完成，包含 {self.index.ntotal} 个向量")