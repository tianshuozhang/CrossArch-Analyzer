import hashlib
import os
import pickle
from typing import Any, Optional
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 默认缓存目录，可以放在项目根目录下的一个隐藏文件夹中
DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.analysis_cache')

class AnalysisCacheManager:
    """
    一个用于缓存代码分析结果的管理器。

    使用文件内容的哈希值作为键，将分析报告（Python对象）序列化后存储在本地文件中。
    这可以极大地提升对未修改文件进行重复分析时的响应速度，并节省LLM API调用成本。
    """

    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR):
        """
        初始化缓存管理器。

        Args:
            cache_dir (str): 用于存储缓存文件的目录路径。
        """
        self.cache_dir = cache_dir
        # 确保缓存目录存在
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir)
                logger.info(f"缓存目录已创建: {self.cache_dir}")
            except OSError as e:
                logger.error(f"创建缓存目录失败: {e}")
                self.cache_dir = None  # 目录创建失败则禁用缓存

    @staticmethod
    def _calculate_hash(content: str) -> str:
        """
        计算字符串内容的SHA256哈希值。

        Args:
            content (str): 要计算哈希值的文件内容。

        Returns:
            str: 内容的十六进制哈希摘要。
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        return hashlib.sha256(content).hexdigest()

    def _get_cache_path(self, key: str) -> str:
        """
        根据键生成完整的缓存文件路径。
        """
        return os.path.join(self.cache_dir, f"{key}.pkl")

    def get(self, content: str) -> Optional[Any]:
        """
        根据文件内容尝试从缓存中获取分析结果。

        Args:
            content (str): 源代码文件的完整内容。

        Returns:
            Optional[Any]: 如果缓存命中，返回反序列化后的分析报告对象；否则返回 None。
        """
        if not self.cache_dir:
            return None # 如果缓存被禁用，直接返回

        key = self._calculate_hash(content)
        cache_path = self._get_cache_path(key)

        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    logger.info(f"缓存命中: {key}")
                    return pickle.load(f)
            except (pickle.UnpicklingError, EOFError, FileNotFoundError) as e:
                logger.warning(f"读取缓存文件失败: {cache_path}, 错误: {e}. 将删除损坏的缓存。")
                os.remove(cache_path) # 删除损坏的缓存文件
        
        logger.info(f"缓存未命中: {key}")
        return None

    def set(self, content: str, report: Any):
        """
        将分析结果存入缓存。

        Args:
            content (str): 源代码文件的完整内容。
            report (Any): 要缓存的分析报告对象。
        """
        if not self.cache_dir:
            return # 如果缓存被禁用，直接返回

        key = self._calculate_hash(content)
        cache_path = self._get_cache_path(key)

        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(report, f)
                logger.info(f"缓存已保存: {key}")
        except (pickle.PicklingError, OSError) as e:
            logger.error(f"保存缓存失败: {cache_path}, 错误: {e}")

    def clear(self):
        """
        清空所有缓存文件。
        """
        if not self.cache_dir or not os.path.exists(self.cache_dir):
            return
        
        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.error(f"删除缓存文件失败: {file_path}, 错误: {e}")
        logger.info("所有缓存已清空。")
        