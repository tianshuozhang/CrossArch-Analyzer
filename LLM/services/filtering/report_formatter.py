"""
报告格式化器模块

负责将筛选和审计结果格式化为可读的文本输出，实现业务逻辑与展示逻辑的分离。
"""
from typing import Dict, List, Tuple


class ScreeningReportFormatter:
    """筛选报告格式化器"""
    
    @staticmethod
    def format_summary(total: int, kept: int, filter_rate: float) -> List[str]:
        """
        格式化执行摘要
        
        Args:
            total: 总文件数
            kept: 保留文件数
            filter_rate: 过滤率
            
        Returns:
            格式化的文本行列表
        """
        lines = []
        lines.append("\n" + "="*70)
        lines.append("架构预筛选报告")
        lines.append("="*70 + "\n")
        lines.append("## 1. 执行摘要")
        lines.append(f"* 输入范围:      {total} 个文件")
        lines.append(f"* 架构文件集:   {kept} 个文件")
        lines.append(f"* 噪声减少率:   {filter_rate:.1f}%")
        
        # 动态生成状态
        if filter_rate > 90:
            status = "已优化 (检测到高信噪比)"
        elif filter_rate > 70:
            status = "已平衡 (应用了中等强度筛选)"
        else:
            status = "复杂架构 (低筛选率)"
        
        lines.append(f"* 状态:          {status}")
        lines.append("-" * 70)
        return lines
    
    @staticmethod
    def format_retention_analysis(stats: Dict, get_top_dirs_func) -> List[str]:
        """
        格式化保留策略分析
        
        Args:
            stats: 统计字典
            get_top_dirs_func: 获取顶级目录的函数
            
        Returns:
            格式化的文本行列表
        """
        lines = []
        lines.append("\n## 2. 保留策略分析")
        
        # 定义保留原因映射（优化：新增 BUILD_CONFIG, BUILD_FILE 和 SIMD_FEATURE）
        reasons = {
            "BUILD_CONFIG": ("构建配置文件", "CMakeLists.txt/Makefile/Kconfig 等构建配置"),
            "BUILD_FILE": ("构建文件白名单", "链接脚本/设备树/独立汇编文件"),
            "DIR_TRUST": ("核心架构信任", "物理抽象层定义 (arch/hal/bsp)"),
            "MACRO_SENSE": ("平台宏启发式", "检测到跨平台兼容性逻辑（字符级状态机）"),
            "ASM_INLINE": ("硬件内联层", "检测到不可移植的汇编指令"),
            "SIMD_FEATURE": ("SIMD 特征检测", "检测到 SIMD 头文件或内联函数"),
            "DRIVER_OPS": ("关键驱动验证", "检测到复杂的 IO/并发操作（含现代 C++ 原语）")
        }
        
        # 遍历所有保留原因
        for reason_key, (title, desc) in reasons.items():
            files = stats["kept"].get(reason_key, [])
            count = len(files)
            if count == 0:
                continue
            
            top_dirs = get_top_dirs_func(files, top_n=3)
            if top_dirs:
                dir_str = ", ".join([f"{d}({c})" for d, c in top_dirs])
            else:
                dir_str = "无"
            
            lines.append(f"[保留] {title}: {count} 个文件")
            lines.append(f"   目录分布: {dir_str}")
            lines.append(f"   原因:     {desc}\n")
        
        # 处理源文件关联
        rescue_files = stats["kept"].get("SOURCE_RESCUE", [])
        if rescue_files:
            rescue_count = len(rescue_files)
            top_dirs = get_top_dirs_func(rescue_files, top_n=3)
            if top_dirs:
                dir_str = ", ".join([f"{d}({c})" for d, c in top_dirs])
            else:
                dir_str = "无"
            
            title = "实现文件关联"
            desc = "与保留头文件配对的源文件"
            lines.append(f"[保留] {title}: {rescue_count} 个文件")
            lines.append(f"   目录分布: {dir_str}")
            lines.append(f"   原因:     {desc}\n")
        
        return lines
    
    @staticmethod
    def format_noise_analysis(stats: Dict, get_top_dirs_func) -> List[str]:
        """
        格式化噪声组件分析
        
        Args:
            stats: 统计字典
            get_top_dirs_func: 获取顶级目录的函数
            
        Returns:
            格式化的文本行列表
        """
        lines = []
        lines.append("## 3. 噪声组件分析（已丢弃）")
        
        # 黑名单分析
        bl_files = stats["dropped"].get("BLACKLIST", [])
        if bl_files:
            top_bl = get_top_dirs_func(bl_files, top_n=5)
            lines.append(f"[丢弃] 测试与工具文件（黑名单）: {len(bl_files)} 个文件")
            if top_bl:
                lines.append(f"   主要来源: {', '.join([f'{d}({c})' for d, c in top_bl])}")
            else:
                lines.append(f"   主要来源: 无")
            lines.append("   操作: 已排除以防止架构图污染\n")
        
        # 无特征分析
        nf_files = stats["dropped"].get("NO_FEATURE", [])
        if nf_files:
            top_nf = get_top_dirs_func(nf_files, top_n=5)
            lines.append(f"[丢弃] 平台无关逻辑: {len(nf_files)} 个文件")
            if top_nf:
                lines.append(f"   主要来源: {', '.join([f'{d}({c})' for d, c in top_nf])}")
            else:
                lines.append(f"   主要来源: 无")
            lines.append("   操作: 已排除（纯业务逻辑/无硬件依赖）\n")
        
        return lines
    
    @staticmethod
    def print_report(lines: List[str]) -> None:
        """
        打印报告
        
        Args:
            lines: 文本行列表
        """
        for line in lines:
            print(line)
        print("="*70 + "\n")


class AuditReportFormatter:
    """审计报告格式化器"""
    
    @staticmethod
    def format_section_header(title: str, width: int = 70) -> List[str]:
        """
        格式化章节标题
        
        Args:
            title: 标题
            width: 宽度
            
        Returns:
            格式化的文本行列表
        """
        return [
            f"\n{'='*width}",
            title,
            f"{'='*width}"
        ]
    
    @staticmethod
    def format_table(headers: List[str], rows: List[List[str]], col_widths: List[int] = None) -> List[str]:
        """
        格式化表格
        
        Args:
            headers: 表头列表
            rows: 数据行列表
            col_widths: 列宽列表
            
        Returns:
            格式化的文本行列表
        """
        lines = []
        if not rows:
            return lines
        
        # 如果没有指定列宽，自动计算
        if col_widths is None:
            col_widths = [max(len(str(h)), max(len(str(r[i])) for r in rows)) for i, h in enumerate(headers)]
        
        # 格式化表头
        header_line = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
        lines.append(header_line)
        lines.append("-" * len(header_line))
        
        # 格式化数据行
        for row in rows:
            row_line = " | ".join(f"{str(r):<{w}}" for r, w in zip(row, col_widths))
            lines.append(row_line)
        
        return lines
    
    @staticmethod
    def format_warning(message: str, items: List[str] = None, max_items: int = 10) -> List[str]:
        """
        格式化警告信息
        
        Args:
            message: 警告消息
            items: 警告项列表
            max_items: 最大显示项数
            
        Returns:
            格式化的文本行列表
        """
        lines = [f"[警告] {message}"]
        if items:
            lines.append("   详情:")
            for item in items[:max_items]:
                lines.append(f"   - {item}")
            if len(items) > max_items:
                lines.append(f"   ... 还有 {len(items) - max_items} 项未显示")
        return lines
    
    @staticmethod
    def format_info(message: str) -> List[str]:
        """
        格式化信息
        
        Args:
            message: 信息消息
            
        Returns:
            格式化的文本行列表
        """
        return [f"[信息] {message}"]
    
    @staticmethod
    def format_pass(message: str) -> List[str]:
        """
        格式化通过信息
        
        Args:
            message: 通过消息
            
        Returns:
            格式化的文本行列表
        """
        return [f"[通过] {message}"]
    
    @staticmethod
    def print_lines(lines: List[str]) -> None:
        """
        打印文本行
        
        Args:
            lines: 文本行列表
        """
        for line in lines:
            print(line)

