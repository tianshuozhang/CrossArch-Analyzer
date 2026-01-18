def sanitize_project_name(name: str) -> str:
    """清理项目名：只保留字母、数字、下划线、连字符"""
    import re

    if not name:
        return ""
    # 移除非法字符，替换空格为下划线
    clean = re.sub(r"[^a-zA-Z0-9_\-]", "", name.replace(" ", "_"))
    return clean.strip("_")[:100]  # 限制长度
