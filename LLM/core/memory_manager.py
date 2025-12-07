import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import json
from pathlib import Path

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
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", storage_path: str = "./LLM/memory/"):
        # 初始化文本嵌入模型

        self.embedding_model = SentenceTransformer(model_name)

        # 创建FAISS向量索引
        self.vector_dim = 384  # all-MiniLM-L6-v2的维度
        self.index = faiss.IndexFlatIP(self.vector_dim)  # 内积相似度
        
        # 记忆存储
        self.memories: List[MemoryItem] = []
        self.memory_vectors = np.empty((0, self.vector_dim))

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)  # 确保目录存在
        
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

    def save_memories(self, agent_id: str, format_type: str = "json") -> str:
        """
        保存记忆到本地文件
        
        Args:
            filename: 文件名（不包含扩展名）
            format_type: 保存格式 ("pickle" 或 "json")
            
        Returns:
            保存的文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{agent_id}_{timestamp}.{format_type}"
        filepath = self.storage_path / filename

        try:
            if format_type == "pickle":
                # 使用pickle保存（推荐，支持完整对象序列化）
                self._save_with_pickle(filepath)
            elif format_type == "json":
                # 使用JSON保存（可读性好，但需要特殊处理）
                self._save_with_json(filepath)
            # 更新最新状态引用
            latest_path = self.storage_path / f"{agent_id}_latest.{format_type}"
            if latest_path.exists():
                latest_path.unlink()
            latest_path.symlink_to(filename)
            
                
        except Exception as e:
            print(f"保存记忆失败: {e}")
            raise
    
    def _save_with_pickle(self, filepath: Path) -> str:
        """使用pickle格式保存记忆"""
        pickle_path = filepath.with_suffix('.pkl')
        
        # 准备保存的数据结构
        save_data = {
            'memories': self.memories,
            'memory_vectors': self.memory_vectors,
            'metadata': {
                'saved_at': datetime.now().isoformat(),
                'memory_count': len(self.memories),
                'vector_dim': self.vector_dim,
                'model_name': self.embedding_model[0].device if hasattr(self.embedding_model[0], 'device') else 'unknown'
            }
        }
        
        with open(pickle_path, 'wb') as f:
            pickle.dump(save_data, f)
        
        print(f"✅ 记忆已保存到: {pickle_path} (共 {len(self.memories)} 条记忆)")
        return str(pickle_path)
    
    def _save_with_json(self, filepath: Path) -> str:
        """使用JSON格式保存记忆（需要特殊处理不可序列化对象）"""
        json_path = filepath.with_suffix('.json')
        
        # 将记忆转换为可JSON序列化的格式
        serializable_memories = []
        for memory in self.memories:
            serializable_memories.append({
                'content': memory.content,
                'timestamp': memory.timestamp.isoformat(),
                'importance': memory.importance,
                'memory_type': memory.memory_type,
                'metadata': memory.metadata
            })
        
        save_data = {
            'memories': serializable_memories,
            'memory_vectors': self.memory_vectors.tolist(),  # 转换为列表
            'metadata': {
                'saved_at': datetime.now().isoformat(),
                'memory_count': len(self.memories),
                'vector_dim': self.vector_dim,
                'format': 'json_serialized'
            }
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 记忆已保存到: {json_path} (JSON格式)")
        return str(json_path)
    
    def load_memories(self, agent_id: str, version: str, filename:str =None, format_type: str = "auto") -> bool:
        """
        从本地文件加载记忆
        
        Args:
            filepath: 文件路径
            format_type: 文件格式 ("auto", "pickle", 或 "json")
            
        Returns:
            是否加载成功
        """

        if not filename:
            filename = f"{agent_id}_{version}.{format_type if format_type != 'auto' else 'pkl'}"
        

        path = self.storage_path / filename
        
        if not path.exists():
            print(f"❌ 文件不存在: {filename}")
            return False
        
        try:
            if format_type == "auto":
                # 根据文件扩展名自动判断格式
                if path.suffix == '.pkl':
                    return self._load_from_pickle(path)
                elif path.suffix == '.json':
                    return self._load_from_json(path)
                else:
                    print(f"❌ 不支持的文件格式: {path.suffix}")
                    return False
            elif format_type == "pickle":
                return self._load_from_pickle(path)
            elif format_type == "json":
                return self._load_from_json(path)
            else:
                print(f"❌ 不支持的格式类型: {format_type}")
                return False
                
        except Exception as e:
            print(f"❌ 加载记忆失败: {e}")
            return False
    
    def _load_from_pickle(self, filepath: Path) -> bool:
        """从pickle文件加载记忆"""
        with open(filepath, 'rb') as f:
            loaded_data = pickle.load(f)
        
        # 恢复记忆数据
        self.memories = loaded_data['memories']
        self.memory_vectors = loaded_data['memory_vectors']
        
        # 重建FAISS索引
        self._rebuild_index()
        
        metadata = loaded_data.get('metadata', {})
        print(f"✅ 记忆加载成功: {len(self.memories)} 条记忆 (保存于: {metadata.get('saved_at', '未知时间')})")
        return True
    
    def _load_from_json(self, filepath: Path) -> bool:
        """从JSON文件加载记忆"""
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        # 将JSON数据转换回MemoryItem对象
        self.memories = []
        for memory_data in loaded_data['memories']:
            memory_item = MemoryItem(
                content=memory_data['content'],
                timestamp=datetime.fromisoformat(memory_data['timestamp']),
                importance=memory_data['importance'],
                memory_type=memory_data['memory_type'],
                metadata=memory_data['metadata']
            )
            self.memories.append(memory_item)
        
        # 恢复向量数据
        self.memory_vectors = np.array(loaded_data['memory_vectors'], dtype='float32')
        
        # 重建FAISS索引
        self._rebuild_index()
        
        metadata = loaded_data.get('metadata', {})
        print(f"✅ 记忆加载成功: {len(self.memories)} 条记忆 (JSON格式)")
        return True
    
    def list_saved_memories(self) -> List[Dict[str, Any]]:
        """
        列出所有已保存的记忆文件
        
        Returns:
            记忆文件信息列表
        """
        memory_files = []
        
        # 查找.pkl和.json文件
        for pattern in ['*.pkl', '*.json']:
            for filepath in self.storage_path.glob(pattern):
                stat = filepath.stat()
                memory_files.append({
                    'filename': filepath.name,
                    'path': str(filepath),
                    'size': stat.st_size,
                    'created_time': datetime.fromtimestamp(stat.st_ctime),
                    'format': 'pickle' if filepath.suffix == '.pkl' else 'json'
                })
        
        # 按创建时间排序
        memory_files.sort(key=lambda x: x['created_time'], reverse=True)
        return memory_files
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        获取记忆统计信息
        
        Returns:
            统计信息字典
        """
        if not self.memories:
            return {'total_memories': 0}
        
        # 按类型统计
        type_stats = {}
        for memory in self.memories:
            type_stats[memory.memory_type] = type_stats.get(memory.memory_type, 0) + 1
        
        # 重要性分布
        importance_scores = [memory.importance for memory in self.memories]
        
        return {
            'total_memories': len(self.memories),
            'type_distribution': type_stats,
            'avg_importance': np.mean(importance_scores) if importance_scores else 0,
            'vector_dimensions': self.memory_vectors.shape,
            'index_size': self.index.ntotal if hasattr(self.index, 'ntotal') else 0
        }
