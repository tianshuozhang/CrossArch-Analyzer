from pathlib import Path


def resource_path(relative_path):
    """获取相对于当前脚本的资源路径"""
    return str(Path(__file__).parent / relative_path)
