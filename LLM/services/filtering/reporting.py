"""
预筛选报告生成器

提供预筛选报告的生成功能，包括：
- 文件加载与预筛选
- 可选的深度审计
- Markdown 和 JSON 格式报告输出
"""

from __future__ import annotations

import io
import json
import os
from contextlib import redirect_stdout
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils import load_project_files
from services.filtering.engine import FilePreScreener
from services.filtering.auditor import ScreeningAuditor


def _safe_relpath(path: str, root: str) -> str:
    """
    安全地将绝对路径转换为相对路径
    
    Args:
        path: 绝对路径
        root: 根目录
        
    Returns:
        相对路径，如果转换失败则返回原路径
    """
    try:
        return os.path.relpath(path, root)
    except Exception:
        return path


def generate_pre_screening_report(
    project_root: str,
    output_dir: str,
    *,
    deep_audit: bool = True,
    llm_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    对指定目录生成预筛选报告（Markdown + JSON），并返回结构化结果。

    Args:
        project_root: 目标项目根目录（如 eigen-5.0.0）
        output_dir: 报告输出目录
        deep_audit: 是否运行审计（会增加运行时间）
        llm_config: 兼容参数，预筛选本身不依赖 LLM，但保留以兼容现有调用方式

    Returns:
        结构化报告数据（可直接 json dump）
    """
    project_root = os.path.abspath(project_root)
    os.makedirs(output_dir, exist_ok=True)

    all_files = load_project_files(project_root)
    pre_screener = FilePreScreener(llm_config or {})

    screening_stdout = io.StringIO()
    with redirect_stdout(screening_stdout):
        kept_files_abs = pre_screener.filter_files(all_files)
    screening_log = screening_stdout.getvalue()

    # 计算保留和丢弃的文件列表
    kept_set = set(kept_files_abs)
    dropped_files_abs = [p for p in all_files.keys() if p not in kept_set]

    # 转换为相对路径以便阅读
    kept_files_rel = sorted(_safe_relpath(p, project_root) for p in kept_files_abs)
    dropped_files_rel = sorted(_safe_relpath(p, project_root) for p in dropped_files_abs)

    # 执行深度审计（如果启用）
    audit_logs, spy_result, content_result = _run_audit_if_enabled(
        deep_audit, all_files, kept_files_abs, project_root
    )

    report_data: Dict[str, Any] = {
        "project_root": project_root,
        "project_name": os.path.basename(project_root.rstrip("\\/")),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input": {
            "total_loaded_files": len(all_files),
            "extensions_loaded": [".h", ".hpp?", ".c", ".cpp"],  # 文档提示用
        },
        "screening": {
            "kept_count": len(kept_files_abs),
            "dropped_count": len(dropped_files_abs),
            "kept_files": kept_files_rel,
            "dropped_files": dropped_files_rel,
            "log": screening_log,
        },
        "audit": {
            "enabled": deep_audit,
            "logs": audit_logs,
            "spy_result": spy_result,
            "content_result": content_result,
        },
    }

    json_path = os.path.join(output_dir, "pre_screening_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    md_path = os.path.join(output_dir, "pre_screening_report.md")
    _write_markdown_report(md_path, report_data)

    # 兼容：保留一份“预筛选结果清单”
    kept_list_path = os.path.join(output_dir, "pre_screening_kept_files.txt")
    with open(kept_list_path, "w", encoding="utf-8") as f:
        for p in kept_files_rel:
            f.write(p + "\n")

    return report_data


def _run_audit_if_enabled(
    deep_audit: bool,
    all_files: Dict[str, str],
    kept_files_abs: List[str],
    project_root: str,
) -> tuple[Dict[str, str], Dict[str, Any], Dict[str, Any]]:
    """
    如果启用深度审计，执行审计并返回结果
    
    Args:
        deep_audit: 是否启用深度审计
        all_files: 所有文件字典
        kept_files_abs: 保留的文件绝对路径列表
        project_root: 项目根目录
        
    Returns:
        (audit_logs, spy_result, content_result) 元组
    """
    audit_logs: Dict[str, str] = {}
    spy_result: Dict[str, Any] = {}
    content_result: Dict[str, Any] = {}

    if not deep_audit:
        return audit_logs, spy_result, content_result

    auditor = ScreeningAuditor(all_files, kept_files_abs)

    # 基础验证审计
    basic_stdout = io.StringIO()
    with redirect_stdout(basic_stdout):
        auditor.run_basic_verification(all_files, kept_files_abs)
    audit_logs["basic_verification"] = basic_stdout.getvalue()

    # 间谍审计
    spy_stdout = io.StringIO()
    with redirect_stdout(spy_stdout):
        spy_result = auditor.run_spy_check(all_files, kept_files_abs)
    audit_logs["spy_check"] = spy_stdout.getvalue()

    # 内容审计（如果有孤儿头文件）
    orphan_headers = spy_result.get("orphan_headers") or []
    if orphan_headers:
        content_stdout = io.StringIO()
        with redirect_stdout(content_stdout):
            symbol_fingerprints, suspicious_files = auditor.run_content_analysis(
                all_files, kept_files_abs, orphan_headers
            )
        audit_logs["content_analysis"] = content_stdout.getvalue()
        content_result = {
            "symbol_fingerprints_count": len(symbol_fingerprints),
            "top_suspicious_files": [
                {"file": _safe_relpath(f, project_root), "hit_count": n}
                for f, n in suspicious_files[:50]
            ],
        }

    # 将审计结果中的路径转换为相对路径
    if "suspicious_files" in spy_result:
        spy_result["suspicious_files"] = [
            _safe_relpath(p, project_root) for p in spy_result.get("suspicious_files", [])
        ]
    if "orphan_headers" in spy_result:
        spy_result["orphan_headers"] = [
            _safe_relpath(p, project_root) for p in spy_result.get("orphan_headers", [])
        ]

    return audit_logs, spy_result, content_result


def _write_markdown_report(md_path: str, data: Dict[str, Any]) -> None:
    """
    生成 Markdown 格式的预筛选报告
    
    Args:
        md_path: Markdown 文件输出路径
        data: 报告数据字典
    """
    screening = data.get("screening", {})
    audit = data.get("audit", {})
    input_data = data.get("input", {})

    total_loaded = input_data.get("total_loaded_files", 0)
    kept = screening.get("kept_count", 0)
    dropped = screening.get("dropped_count", 0)
    drop_rate = (dropped / total_loaded * 100.0) if total_loaded else 0.0

    kept_files: List[str] = screening.get("kept_files", [])
    dropped_files: List[str] = screening.get("dropped_files", [])

    with open(md_path, "w", encoding="utf-8") as f:
        # 报告头部
        _write_markdown_header(f, data)
        
        # 总览统计
        _write_markdown_overview(f, total_loaded, kept, dropped, drop_rate)
        
        # 预筛选日志
        _write_markdown_screening_log(f, screening)
        
        # 文件清单
        _write_markdown_file_lists(f, kept_files, dropped_files)
        
        # 审计结果（如果启用）
        if audit.get("enabled"):
            _write_markdown_audit_section(f, audit)


def _write_markdown_header(f, data: Dict[str, Any]) -> None:
    """
    写入 Markdown 报告头部
    
    Args:
        f: 文件对象
        data: 报告数据字典
    """
    f.write(f"# 预筛选分析报告：{data.get('project_name', '(unknown)')}\n\n")
    f.write(f"- 项目根目录：`{data.get('project_root', '')}`\n")
    f.write(f"- 生成时间：`{data.get('generated_at', '')}`\n\n")


def _write_markdown_overview(f, total_loaded: int, kept: int, dropped: int, drop_rate: float) -> None:
    """
    写入总览统计
    
    Args:
        f: 文件对象
        total_loaded: 总加载文件数
        kept: 保留文件数
        dropped: 丢弃文件数
        drop_rate: 过滤率
    """
    f.write("## 总览\n\n")
    f.write(f"- 总加载文件数（C/C++）：**{total_loaded}**\n")
    f.write(f"- 保留文件数：**{kept}**\n")
    f.write(f"- 丢弃文件数：**{dropped}**\n")
    f.write(f"- 过滤率：**{drop_rate:.1f}%**\n\n")


def _write_markdown_screening_log(f, screening: Dict[str, Any]) -> None:
    """
    写入预筛选日志
    
    Args:
        f: 文件对象
        screening: 预筛选数据字典
    """
    f.write("## 预筛选日志（原始输出）\n\n")
    f.write("```text\n")
    f.write((screening.get("log") or "").strip() + "\n")
    f.write("```\n\n")


def _write_markdown_file_lists(f, kept_files: List[str], dropped_files: List[str]) -> None:
    """
    写入文件清单
    
    Args:
        f: 文件对象
        kept_files: 保留文件列表
        dropped_files: 丢弃文件列表
    """
    f.write("## 清单（节选）\n\n")
    
    # 保留文件列表
    f.write("### 保留文件 Top 50\n\n")
    for p in kept_files[:50]:
        f.write(f"- `{p}`\n")
    if len(kept_files) > 50:
        f.write(f"\n> 还有 {len(kept_files) - 50} 个未展开，详见 `pre_screening_report.json` 或 `pre_screening_kept_files.txt`。\n")

    # 丢弃文件列表
    f.write("\n### 丢弃文件 Top 50\n\n")
    for p in dropped_files[:50]:
        f.write(f"- `{p}`\n")
    if len(dropped_files) > 50:
        f.write(f"\n> 还有 {len(dropped_files) - 50} 个未展开，详见 `pre_screening_report.json`。\n")


def _write_markdown_audit_section(f, audit: Dict[str, Any]) -> None:
    """
    写入审计结果部分
    
    Args:
        f: 文件对象
        audit: 审计数据字典
    """
    f.write("\n## 审计（可选）\n\n")
    logs = audit.get("logs", {}) or {}

    audit_sections = [
        ("basic_verification", "基础验证审计输出"),
        ("spy_check", "反向引用审计输出"),
        ("content_analysis", "内容审计输出（孤儿头文件 + 符号匹配）"),
    ]

    for log_key, title in audit_sections:
        if log_key in logs:
            f.write(f"### {title}\n\n")
            f.write("```text\n")
            f.write(logs[log_key].strip() + "\n")
            f.write("```\n\n")


