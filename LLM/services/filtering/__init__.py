"""
文件筛选模块

提供文件预筛选、审计和报告生成功能。

主要组件：
    - FilePreScreener: 文件预筛选器，基于位置的信任策略进行文件筛选
    - ScreeningAuditor: 筛选审计器，提供多种审计方法验证筛选结果
    - generate_pre_screening_report: 生成预筛选报告（Markdown + JSON）
    
辅助模块：
    - report_formatter: 报告格式化器，负责格式化输出
    - statistics: 统计工具模块，提供通用的统计分析功能
"""
from .engine import FilePreScreener
from .auditor import ScreeningAuditor
from .reporting import generate_pre_screening_report

__all__ = ['FilePreScreener', 'ScreeningAuditor', 'generate_pre_screening_report']

