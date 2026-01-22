"""
文件筛选审计模块

整合了基础验证、反向引用审计和内容审计功能，用于验证和优化筛选结果。
"""
import os
import re
import random
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any

from .statistics import (
    DirectoryStatistics,
    FileTypeStatistics,
    FileSizeStatistics,
    KeywordStatistics
)
from .report_formatter import AuditReportFormatter


class ScreeningAuditor:
    """
    筛选审计器
    
    提供多种审计方法来验证和优化筛选结果，包括：
    - 基础验证审计：目录覆盖率、关键词检查、文件类型分布等
    - 反向引用审计：检测被丢弃但引用保留头文件的源文件
    - 内容审计：分析孤儿头文件和符号匹配情况
    """
    
    def __init__(self, all_files: Dict[str, str], kept_files: List[str]):
        """
        初始化审计器
        
        Args:
            all_files: 所有文件的字典，键为文件路径，值为文件内容
            kept_files: 被保留的文件路径列表
        """
        self.all_files = all_files
        self.kept_files = set(kept_files)
        self.dropped_files = [f for f in all_files.keys() if f not in self.kept_files]
    
    def run_basic_verification(self, all_files: Dict[str, str], kept_files: List[str]) -> None:
        """
        运行基础验证审计
        
        对筛选结果进行基础验证，包括目录覆盖率、关键词检查、
        文件类型分布、核心架构目录检查和文件大小分布分析。
        
        Args:
            all_files: 所有文件路径字典，键为文件路径，值为文件内容
            kept_files: 筛选后保留的文件路径列表
        """
        all_file_paths = list(all_files.keys())
        kept_set = set(kept_files)
        dropped_files = [f for f in all_file_paths if f not in kept_set]
        
        formatter = AuditReportFormatter()
        lines = []
        
        # 报告头部
        lines.extend(formatter.format_section_header("筛选器审计报告"))
        lines.append(f"总体数据: 总数 {len(all_file_paths)} | 保留 {len(kept_files)} | 丢弃 {len(dropped_files)}")
        if len(all_file_paths) > 0:
            lines.append(f"过滤率: {len(dropped_files)/len(all_file_paths)*100:.1f}%")

        # 1. 目录覆盖率分析
        lines.append(f"\n[分析 1] 关键目录保留率 (Directory Coverage)")
        lines.append("说明: 检查核心目录是否被过度过滤，或者驱动目录是否被完全忽略")
        
        dir_stats = DirectoryStatistics.calculate_directory_coverage(
            all_file_paths, kept_set, max_depth=2
        )
        sorted_dirs = sorted(dir_stats.items(), key=lambda x: x[1]['total'], reverse=True)[:15]
        
        table_rows = []
        for d, stat in sorted_dirs:
            ratio = (stat['kept'] / stat['total']) * 100 if stat['total'] > 0 else 0
            table_rows.append([d, str(stat['total']), str(stat['kept']), f"{ratio:.1f}%"])
        
        lines.extend(formatter.format_table(
            ["目录路径", "总数", "保留", "保留率"],
            table_rows,
            col_widths=[40, 5, 5, 8]
        ))

        # 2. 关键词检查
        lines.append(f"\n[分析 2] 丢弃列表关键词检查 (Dropped Keyword Check)")
        lines.append("说明: 如果在被丢弃的文件路径里发现了这些词，可能是误过滤")
        
        caught_traps = KeywordStatistics.find_suspicious_files(dropped_files)
        
        if caught_traps:
            sample_size = min(10, len(caught_traps))
            sample_files = random.sample(caught_traps, sample_size) if sample_size > 0 else []
            lines.extend(formatter.format_warning(
                f"在丢弃列表中发现了 {len(caught_traps)} 个包含敏感词的文件",
                [f"[已丢弃] {f}" for f in sample_files]
            ))
        else:
            lines.extend(formatter.format_pass("丢弃列表中未发现明显的高危关键词"))

        # 3. 文件扩展名分布分析
        lines.append(f"\n[分析 3] 文件类型分布 (File Type Distribution)")
        lines.append("说明: 检查不同文件类型的保留率是否合理")
        
        ext_stats = FileTypeStatistics.calculate_extension_stats(all_file_paths, kept_set)
        table_rows = []
        for ext, stat in sorted(ext_stats.items(), key=lambda x: x[1]['total'], reverse=True):
            ratio = (stat['kept'] / stat['total']) * 100 if stat['total'] > 0 else 0
            table_rows.append([ext, str(stat['total']), str(stat['kept']), f"{ratio:.1f}%"])
        
        lines.extend(formatter.format_table(
            ["文件类型", "总数", "保留", "保留率"],
            table_rows,
            col_widths=[15, 5, 5, 8]
        ))

        # 4. 核心架构目录检查
        lines.append(f"\n[分析 4] 核心架构目录检查 (Core Architecture Directories)")
        lines.append("说明: 检查关键架构相关目录的保留情况")
        
        critical_dirs = ["arch", "hal", "bsp", "driver", "kernel", "os", "platform"]
        critical_stats = DirectoryStatistics.calculate_critical_directory_stats(
            all_file_paths, kept_set, critical_dirs
        )
        
        if critical_stats:
            table_rows = []
            for dir_name, stat in sorted(critical_stats.items(), key=lambda x: x[1]['total'], reverse=True):
                table_rows.append([
                    dir_name,
                    str(stat['total']),
                    str(stat['kept']),
                    f"{stat['ratio']:.1f}%"
                ])
            
            lines.extend(formatter.format_table(
                ["目录名", "总数", "保留", "保留率"],
                table_rows,
                col_widths=[15, 5, 5, 8]
            ))
            
            fully_dropped = [
                d for d, s in critical_stats.items() 
                if s['kept'] == 0 and s['total'] > 0
            ]
            if fully_dropped:
                dropped_items = [
                    f"{d}/ (共 {critical_stats[d]['total']} 个文件)" 
                    for d in fully_dropped
                ]
                lines.extend(formatter.format_warning(
                    "以下核心目录的所有文件都被过滤了",
                    dropped_items
                ))
        else:
            lines.extend(formatter.format_info("未发现常见的核心架构目录"))

        # 5. 文件大小分布分析
        lines.append(f"\n[分析 5] 文件大小分布 (File Size Distribution)")
        lines.append("说明: 检查大文件和小文件的保留率差异")
        
        size_stats = FileSizeStatistics.calculate_size_stats(
            all_file_paths, all_files, kept_set
        )
        
        if size_stats:
            table_rows = []
            for size_label, stat in size_stats.items():
                table_rows.append([
                    size_label,
                    str(stat['total']),
                    str(stat['kept']),
                    f"{stat['ratio']:.1f}%"
                ])
            
            lines.extend(formatter.format_table(
                ["大小范围", "总数", "保留", "保留率"],
                table_rows,
                col_widths=[15, 5, 5, 8]
            ))

        lines.append(f"\n{'='*70}")
        lines.append("筛选器审计完成")
        lines.append(f"{'='*70}\n")
        
        formatter.print_lines(lines)
    
    def run_spy_check(self, all_files: Dict[str, str], kept_files: List[str]) -> Dict[str, Any]:
        """
        运行反向引用审计
        
        检测被丢弃但引用了保留头文件的源文件，这些文件可能是被误过滤的实现文件。
        
        Args:
            all_files: 所有文件的字典，键为文件路径，值为文件内容
            kept_files: 被保留的文件路径列表
            
        Returns:
            包含可疑文件和孤儿头文件的字典
        """
        kept_set = set(kept_files)
        dropped_files = [f for f in all_files.keys() if f not in kept_set]
        
        # 步骤1：构建保留头文件索引
        vip_headers = {}
        for f in kept_files:
            if f.endswith(('.h', '.hpp')):
                fname = os.path.basename(f)
                if fname not in vip_headers:
                    vip_headers[fname] = []
                vip_headers[fname].append(f)
        
        print(f"\n{'='*70}")
        print("反向引用审计")
        print(f"{'='*70}")
        print(f"保留头文件索引: {len(vip_headers)} 个唯一文件名")
        print(f"监控范围: {len(dropped_files)} 个被丢弃的文件")
        
        # 步骤2：扫描被丢弃的文件
        suspicious_files = []
        include_pattern = re.compile(r'#include\s*[<"]([^">]+)[">]')
        
        scanned_count = 0
        for f in dropped_files:
            if not f.endswith(('.c', '.cpp', '.cc', '.cxx')):
                continue
            
            scanned_count += 1
            content = all_files.get(f, "")
            includes = include_pattern.findall(content)
            
            for inc in includes:
                inc_name = os.path.basename(inc)
                if inc_name in vip_headers:
                    linked_header = vip_headers[inc_name][0]
                    suspicious_files.append({
                        "suspect": f,
                        "linked_to": linked_header,
                        "include_name": inc_name
                    })
                    break
        
        # 步骤3：生成报告
        print(f"\n扫描完成: 检查了 {scanned_count} 个被丢弃的源文件")
        print(f"\n[反向引用报告] 发现 {len(suspicious_files)} 个可疑的被误过滤文件")
        print("   说明: 这些文件被丢弃，但它们引用了被保留的头文件")
        print("   可能原因: 它们很可能是缺失的实现文件\n")
        
        if suspicious_files:
            print(f"前 20 个最可疑的误过滤文件 (Top Suspicious False Negatives):")
            print("-" * 70)
            for i, item in enumerate(suspicious_files[:20], 1):
                suspect_name = os.path.basename(item['suspect'])
                header_name = os.path.basename(item['linked_to'])
                print(f"   {i:2d}. [可疑] {suspect_name}")
                print(f"       └── includes '{header_name}' (from {os.path.dirname(item['linked_to'])})")
                print(f"       [路径] {item['suspect']}")
                if i < min(20, len(suspicious_files)):
                    print()
            
            if len(suspicious_files) > 20:
                print(f"\n   ... 还有 {len(suspicious_files) - 20} 个可疑文件未显示")
        else:
            print("   [通过] 未发现可疑文件（所有被丢弃的源文件都没有引用保留的头文件）")
        
        # 步骤4：计算孤儿率
        linked_headers = set()
        for item in suspicious_files:
            linked_headers.add(item['linked_to'])
        
        orphan_headers = []
        total_headers = len([f for f in kept_files if f.endswith(('.h', '.hpp'))])
        for f in kept_files:
            if f.endswith(('.h', '.hpp')):
                if f not in linked_headers:
                    orphan_headers.append(f)
        
        orphan_rate = (len(orphan_headers) / total_headers) * 100 if total_headers > 0 else 0
        
        print(f"\n[孤儿率分析]")
        print(f"   - 保留的头文件总数: {total_headers}")
        print(f"   - 找到关联实现的头文件: {len(linked_headers)}")
        print(f"   - 孤儿头文件（无关联实现）: {len(orphan_headers)}")
        print(f"   - 孤儿率: {orphan_rate:.1f}%")
        
        if orphan_headers and len(orphan_headers) <= 10:
            print(f"\n   孤儿头文件列表:")
            for h in orphan_headers[:10]:
                print(f"      - {os.path.basename(h)} ({h})")
        elif orphan_headers:
            print(f"\n   前 10 个孤儿头文件:")
            for h in orphan_headers[:10]:
                print(f"      - {os.path.basename(h)} ({h})")
            print(f"      ... 还有 {len(orphan_headers) - 10} 个")
        
        print(f"\n{'='*70}")
        print("反向引用审计完成")
        print(f"{'='*70}\n")
        
        return {
            'suspicious_files': [x['suspect'] for x in suspicious_files],
            'orphan_headers': orphan_headers
        }
    
    def run_content_analysis(self, all_files: Dict[str, str], kept_files: List[str], 
                            orphan_headers: List[str] = None) -> Tuple[Set[str], List[Tuple[str, int]]]:
        """
        运行内容审计
        
        分析孤儿头文件的特征，并检测被丢弃文件中是否包含保留头文件中的符号，
        以识别可能被误过滤的实现文件。
        
        Args:
            all_files: 所有文件的字典，键为文件路径，值为文件内容
            kept_files: 被保留的文件路径列表
            orphan_headers: 孤儿头文件列表（可选，如果不提供则自动计算）
            
        Returns:
            (符号指纹集合, 可疑文件列表) 元组
        """
        kept_set = set(kept_files)
        dropped_files = [f for f in all_files.keys() if f not in kept_set]
        
        if orphan_headers is None:
            orphan_headers = [f for f in kept_files if f.endswith(('.h', '.hpp'))]
        
        # 步骤1：分析孤儿头文件
        print(f"\n{'='*70}")
        print("内容审计 - 孤儿头文件分析")
        print(f"{'='*70}")
        print(f"分析目标: {len(orphan_headers)} 个孤儿头文件")
        
        header_only_traits = {
            "template": 0,
            "inline": 0,
            "virtual": 0,
            "has_implementation": 0
        }
        
        symbol_fingerprints = set()
        excluded_keywords = {
            'if', 'for', 'while', 'switch', 'return', 'sizeof', 'static_cast',
            'dynamic_cast', 'const_cast', 'reinterpret_cast', 'new', 'delete',
            'throw', 'catch', 'try', 'else', 'case', 'default', 'break', 'continue'
        }
        
        function_pattern = re.compile(
            r'\b(?:'
            r'(?:template\s*<[^>]*>\s*)?'
            r'(?:inline\s+|static\s+|constexpr\s+|explicit\s+)*'
            r'(?:[a-zA-Z_][a-zA-Z0-9_]*\s+)?'
            r'([a-zA-Z_][a-zA-Z0-9_]{4,})'
            r'\s*\('
            r')'
        )
        
        for f in orphan_headers:
            content = all_files.get(f, "")
            
            if re.search(r'\btemplate\s*<', content):
                header_only_traits["template"] += 1
            
            if re.search(r'\binline\s+', content):
                header_only_traits["inline"] += 1
            
            if re.search(r'\bvirtual\s+', content):
                header_only_traits["virtual"] += 1
            
            if re.search(r'\{\s*[^}]{10,}\}', content) or re.search(r'template\s*<[^>]*>\s*[^{]+\{', content):
                header_only_traits["has_implementation"] += 1
            
            matches = function_pattern.findall(content)
            for match in matches:
                func_name = match if isinstance(match, str) else match[0] if match else ""
                if func_name and func_name not in excluded_keywords and len(func_name) >= 5:
                    symbol_fingerprints.add(func_name)
        
        total_headers = len(orphan_headers)
        
        print(f"\n[孤儿头文件特征分析] Header-Only 特征:")
        print(f"   - 包含 template:     {header_only_traits['template']:3d}/{total_headers} ({header_only_traits['template']/total_headers*100:.1f}%)")
        print(f"   - 包含 inline:       {header_only_traits['inline']:3d}/{total_headers} ({header_only_traits['inline']/total_headers*100:.1f}%)")
        print(f"   - 包含 virtual:      {header_only_traits['virtual']:3d}/{total_headers} ({header_only_traits['virtual']/total_headers*100:.1f}%)")
        print(f"   - 包含实现代码:      {header_only_traits['has_implementation']:3d}/{total_headers} ({header_only_traits['has_implementation']/total_headers*100:.1f}%)")
        
        header_only_count = sum(1 for f in orphan_headers 
                               if re.search(r'\btemplate\s*<', all_files.get(f, "")) or 
                                  re.search(r'\binline\s+', all_files.get(f, "")))
        
        header_only_rate = (header_only_count / total_headers * 100) if total_headers > 0 else 0
        
        print(f"\nHeader-Only 疑似率: {header_only_rate:.1f}%")
        print(f"   说明: 高百分比意味着这些头文件很可能是模板/内联实现，")
        print(f"      不需要单独的 .cpp 文件，这是正常的。")
        
        print(f"\n提取的符号指纹: {len(symbol_fingerprints)} 个函数名")
        if len(symbol_fingerprints) <= 20:
            print(f"   示例: {', '.join(list(symbol_fingerprints)[:20])}")
        else:
            print(f"   示例: {', '.join(list(symbol_fingerprints)[:20])} ...")
        
        # 步骤2：符号匹配检测
        print(f"\n{'='*70}")
        print("内容审计 - 符号匹配检测")
        print(f"{'='*70}")
        print(f"扫描范围: {len(dropped_files)} 个被丢弃的文件")
        print(f"符号库: {len(symbol_fingerprints)} 个关键符号")
        
        suspicious_files = []
        source_files = [f for f in dropped_files if f.endswith(('.c', '.cpp', '.cc', '.cxx'))]
        
        for f in source_files:
            content = all_files.get(f, "")
            hit_count = 0
            matched_symbols = []
            
            for sym in symbol_fingerprints:
                pattern = re.compile(r'\b' + re.escape(sym) + r'\s*[({]')
                if pattern.search(content):
                    hit_count += 1
                    matched_symbols.append(sym)
            
            if hit_count >= 3:
                suspicious_files.append({
                    "file": f,
                    "hit_count": hit_count,
                    "matched_symbols": matched_symbols[:10]
                })
        
        suspicious_files.sort(key=lambda x: x['hit_count'], reverse=True)
        
        print(f"扫描完成: 检查了 {len(source_files)} 个被丢弃的源文件")
        print(f"\n[符号匹配报告] 发现 {len(suspicious_files)} 个可疑文件")
        print("   说明: 这些被丢弃的文件包含大量保留头文件中的符号，")
        print("      可能是被误过滤的实现文件\n")
        
        if suspicious_files:
            print(f"Top 20 可疑文件 (按符号匹配数排序):")
            print("-" * 70)
            for i, item in enumerate(suspicious_files[:20], 1):
                file_name = os.path.basename(item['file'])
                print(f"   {i:2d}. [可疑] [{item['hit_count']:2d} 个符号] {file_name}")
                print(f"       [路径] {item['file']}")
                if item['matched_symbols']:
                    symbols_str = ', '.join(item['matched_symbols'][:5])
                    if len(item['matched_symbols']) > 5:
                        symbols_str += f" ... (+{len(item['matched_symbols'])-5} 个)"
                    print(f"       [匹配符号] {symbols_str}")
                print()
        else:
            print("   [通过] 未发现可疑文件（所有被丢弃的文件都没有大量匹配保留头文件的符号）")
        
        print(f"{'='*70}")
        print("内容审计完成")
        print(f"{'='*70}\n")
        
        return symbol_fingerprints, [(item['file'], item['hit_count']) for item in suspicious_files]



