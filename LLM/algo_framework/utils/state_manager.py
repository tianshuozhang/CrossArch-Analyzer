from utils.rela_path import resource_path

import json
import pickle
from typing import Dict, Any, Optional, List
from pathlib import Path
from json import JSONEncoder
from datetime import datetime, date


class AgentStateEncoder(JSONEncoder):
    """专用于序列化Agent状态的自定义JSON编码器"""

    def default(self, obj):
        # 1. 首先处理日期时间对象[1](@ref)[2](@ref)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()  # 转换为ISO格式字符串[1](@ref)[5](@ref)

        # 2. 处理你的 CodeClassification 对象
        # 假设你的类名为 CodeClassification，请根据实际情况调整
        elif hasattr(obj, "__dict__"):
            # 尝试将对象转换为字典[7](@ref)[8](@ref)
            return obj.__dict__

        # 3. 如果遇到其他无法处理的类型，调用父类方法（会抛出TypeError）
        return super().default(obj)


class StateManager:
    """状态管理器：负责Agent状态的序列化、持久化和加载"""

    def __init__(self, storage_path: str = resource_path("../state")):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

    def save_state(
        self, agent_id: str, state: Dict[str, Any], format_type: str = "json"
    ) -> str:
        """
        保存Agent状态到文件

        Args:
            agent_id: Agent唯一标识
            state: 状态数据
            format_type: 序列化格式 (json/pickle)

        Returns:
            保存的文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{agent_id}_{timestamp}.{format_type}"
        filepath = self.storage_path / filename

        try:
            if format_type == "json":
                with open(filepath, "w", encoding="utf-8") as f:
                    # 使用自定义编码器
                    json.dump(
                        state, f, indent=2, ensure_ascii=False, cls=AgentStateEncoder
                    )
            else:
                # Pickle序列化（二进制，支持复杂对象）
                with open(filepath, "wb") as f:
                    pickle.dump(state, f)

            # 更新最新状态引用
            latest_path = self.storage_path / f"{agent_id}_latest.{format_type}"
            if latest_path.exists():
                latest_path.unlink()
            latest_path.symlink_to(filename)

            return str(filepath)

        except Exception as e:
            raise Exception(f"状态保存失败: {e}")

    def load_state(
        self, agent_id: str, format_type: str = "json", version: str = "latest"
    ) -> Optional[Dict[str, Any]]:
        """
        加载Agent状态

        Args:
            agent_id: Agent唯一标识
            format_type: 序列化格式
            version: 版本标识（latest或具体时间戳）

        Returns:
            状态数据字典
        """
        if version == "latest":
            filename = f"{agent_id}_latest.{format_type}"
        else:
            filename = f"{agent_id}_{version}.{format_type}"

        filepath = self.storage_path / filename

        if not filepath.exists():
            return None

        try:
            if format_type == "json":
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                with open(filepath, "rb") as f:
                    return pickle.load(f)

        except Exception as e:
            raise Exception(f"状态加载失败: {e}")

    def serialize_to_bytes(self, state: Dict[str, Any]) -> bytes:
        """将状态序列化为字节流，适合网络传输"""
        return pickle.dumps(state)

    def deserialize_from_bytes(self, data: bytes) -> Dict[str, Any]:
        """从字节流反序列化状态"""
        return pickle.loads(data)

    def get_state_history(self, agent_id: str) -> List[Dict[str, str]]:
        """获取Agent的状态历史记录"""
        pattern = f"{agent_id}_*.json"
        history = []

        for filepath in self.storage_path.glob(pattern):
            if "latest" not in filepath.name:
                stat = filepath.stat()
                history.append(
                    {
                        "filename": filepath.name,
                        "created_time": datetime.fromtimestamp(stat.st_ctime),
                        "size": stat.st_size,
                    }
                )

        return sorted(history, key=lambda x: x["created_time"], reverse=True)
