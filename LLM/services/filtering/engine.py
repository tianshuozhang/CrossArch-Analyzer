"""
文件预筛选引擎
基于位置的信任策略进行文件筛选
"""
import re
import os
from typing import Dict, List
from collections import defaultdict, Counter


class FilePreScreener:
    """
    文件智能预筛选器：基于位置的信任策略（平衡筛选）
    
    区分核心架构目录和普通驱动目录，实施差异化的信任策略。
    
    筛选逻辑：
    1. 核心目录直通：arch/, hal/, bsp/, platform/ 等 -> 直接保留
    2. 宏定义嗅探：包含平台差异化宏 -> 直接保留
    3. 汇编直通：包含 asm/__asm__ -> 保留
    4. 驱动层交叉验证：driver/dev/sys 路径需要 CRITICAL_OPS 才保留
    5. 源文件连坐：如果头文件被保留，对应的源文件也自动保留
    """
    
    # 类常量：核心架构目录模式
    ARCH_DIRECTORY_PATTERN = re.compile(
        r"(?i)(arch[/\\]|hal[/\\]|bsp[/\\]|platform[/\\]|mach-|board[/\\])"
    )
    
    # 类常量：平台差异化宏模式
    PLATFORM_MACRO_PATTERN = re.compile(
        r"#\s*(ifdef|if\s+defined|ifndef).*(ARM|X86|MIPS|RISCV|WIN32|LINUX|APPLE|RTOS|SOC|ARCH|__arm__|__x86_64__|__riscv|__mips__)",
        re.IGNORECASE
    )
    
    # 类常量：汇编代码模式
    ASM_PATTERN = re.compile(r"\b(asm|__asm__)\b")
    
    # 类常量：黑名单模式
    BLACKLIST_PATTERN = re.compile(
        r"(?i)(test|mock|doc|docs|tools|example|examples|sample|samples|script)"
    )
    
    # 类常量：驱动上下文模式
    DRIVER_CONTEXT_PATTERN = re.compile(r"(?i)(driver|dev|sys|module|kernel)")
    
    # 类常量：关键操作模式
    CRITICAL_OPS_PATTERN = re.compile(
        r"\b(mutex|spinlock|atomic|dma|phys_|virt_|ioremap|ioctl|interrupt|irq|barrier|semaphore|mmap|wmb|rmb|mb)\b"
    )
    
    # 类常量：源文件扩展名
    SOURCE_EXTENSIONS = ['.c', '.cpp', '.cc', '.cxx']
    
    def __init__(self, llm_config: Dict = None):
        """
        初始化文件预筛选器
        
        Args:
            llm_config: 保留此参数以兼容现有调用代码，但不再使用
        """
        pass
    
    def _is_arch_directory(self, path: str) -> bool:
        """
        检测是否为核心架构目录
        
        这些目录下的内容默认是架构相关的，即使只是一行 struct 定义。
        
        Args:
            path: 文件路径
            
        Returns:
            True 表示是核心架构目录
        """
        return bool(self.ARCH_DIRECTORY_PATTERN.search(path))
    
    def _has_platform_macros(self, content: str) -> bool:
        """
        检测是否包含平台差异化宏
        
        条件编译是架构差异最直接的体现。
        
        Args:
            content: 文件内容
            
        Returns:
            True 表示包含平台差异化宏
        """
        return bool(self.PLATFORM_MACRO_PATTERN.search(content))
    
    def _get_top_dirs(self, file_list: List[str], top_n: int = 3) -> List[tuple]:
        """
        辅助函数：从文件列表中提取出现频率最高的相对目录。
        自动去除公共前缀，只显示有意义的子目录。
        
        Args:
            file_list: 文件路径列表
            top_n: 返回前 N 个目录
            
        Returns:
            目录及其出现次数的元组列表，按频率降序排列
        """
        if not file_list:
            return []

        # 1. 尝试找到所有文件的公共根目录
        try:
            # os.path.commonpath 可能会抛出异常（如果路径混合了不同驱动器）
            # 或者如果是空列表，前面已经处理了
            common_root = os.path.commonpath(file_list)
            
            # 如果 common_root 本身就是一个文件（单一文件情况），取其目录
            if os.path.isfile(common_root):
                common_root = os.path.dirname(common_root)
        except ValueError:
            common_root = ""

        # 2. 计算相对路径并提取有意义的层级
        meaningful_dirs = []
        for f in file_list:
            try:
                # 获取相对路径 (e.g., "eigen/src/Core/util.h")
                if common_root:
                    rel_path = os.path.relpath(f, start=common_root)
                else:
                    rel_path = f
                
                # 提取目录部分
                d = os.path.dirname(rel_path)
                
                # 标准化分隔符
                d = d.replace("\\", "/")
                
                # 如果是根目录 (.)，标记为 Root
                if d == "." or d == "":
                    meaningful_dirs.append("[Root]")
                    continue

                # 提取前两级目录 (e.g., "eigen/src") 以避免过长
                parts = d.split("/")
                if len(parts) > 2:
                    # 取前两级，这样显示更聚合
                    simplified = f"{parts[0]}/{parts[1]}"
                    meaningful_dirs.append(simplified)
                else:
                    meaningful_dirs.append(d)

            except Exception:
                # 兜底：如果相对路径计算失败，回退到目录名
                meaningful_dirs.append(os.path.dirname(f))

        return Counter(meaningful_dirs).most_common(top_n)
    
    def _generate_professional_report(self, total: int, kept: int, stats: Dict) -> None:
        """
        生成并打印专业的架构审计报告
        
        Args:
            total: 总文件数
            kept: 保留文件数
            stats: 统计字典，包含 kept 和 dropped 两个子字典
        """
        dropped = total - kept
        filter_rate = (dropped / total * 100) if total > 0 else 0
        
        print("\n" + "="*70)
        print("🛡️  PHASE 1.5 ARCHITECTURE PRE-SCREENING REPORT")
        print("="*70 + "\n")
        
        # 1. Executive Summary
        print("## 1. Executive Summary")
        print(f"* Input Scope:      {total} files")
        print(f"* Architecture Set: {kept} files")
        print(f"* Noise Reduction:  {filter_rate:.1f}%")
        
        # 动态生成结论
        if filter_rate > 90:
            status = "🟢 Optimized (High Signal-to-Noise Ratio detected)"
        elif filter_rate > 70:
            status = "🟡 Balanced (Moderate filtering applied)"
        else:
            status = "🔴 Complex Architecture detected (Low filtering rate)"
        
        print(f"* Status:           {status}")
        print("-" * 70)
        
        # 2. Retention Strategy Analysis
        print("\n## 2. Retention Strategy Analysis")
        
        # 定义文案映射（排除 SOURCE_RESCUE，单独处理）
        reasons = {
            "DIR_TRUST": ("Core Architecture Trust", "Physical abstraction layer definitions (arch/hal/bsp)."),
            "MACRO_SENSE": ("Platform Macro Heuristics", "Cross-platform compatibility logic detected."),
            "ASM_INLINE": ("Hardware Intrinsic Layer", "Non-portable assembly instructions detected."),
            "DRIVER_OPS": ("Critical Driver Verification", "Complex IO/Concurrency operations detected.")
        }
        
        # 遍历所有保留原因（排除 SOURCE_RESCUE，单独处理）
        for reason_key, (title, desc) in reasons.items():
            files = stats["kept"].get(reason_key, [])
            count = len(files)
            if count == 0:
                continue
            
            top_dirs = self._get_top_dirs(files, top_n=3)
            if top_dirs:
                dir_str = ", ".join([f"{d}({c})" for d, c in top_dirs])
            else:
                dir_str = "None"
            
            print(f"✅ {title}: {count} files")
            print(f"   Fingerprint: {dir_str}")
            print(f"   Rationale:   {desc}\n")
        
        # 处理源文件连坐（单独处理）
        rescue_files = stats["kept"].get("SOURCE_RESCUE", [])
        if rescue_files:
            rescue_count = len(rescue_files)
            top_dirs = self._get_top_dirs(rescue_files, top_n=3)
            if top_dirs:
                dir_str = ", ".join([f"{d}({c})" for d, c in top_dirs])
            else:
                dir_str = "N/A"
            
            title = "Implementation Rescue"
            desc = "Source files paired with retained headers."
            print(f"✅ {title}: {rescue_count} files")
            print(f"   Fingerprint: {dir_str}")
            print(f"   Rationale:   {desc}\n")
        
        # 3. Noise Component Analysis (Dropped)
        print("## 3. Noise Component Analysis (Dropped)")
        
        # Blacklist Analysis
        bl_files = stats["dropped"].get("BLACKLIST", [])
        if bl_files:
            top_bl = self._get_top_dirs(bl_files, top_n=5)
            print(f"🛑 Testing & Artifacts (Blacklist): {len(bl_files)} files")
            if top_bl:
                print(f"   Primary Sources: {', '.join([f'{d}({c})' for d, c in top_bl])}")
            else:
                print(f"   Primary Sources: None")
            print("   Action: Excluded to prevent architectural graph pollution.\n")
        
        # No Feature Analysis
        nf_files = stats["dropped"].get("NO_FEATURE", [])
        if nf_files:
            top_nf = self._get_top_dirs(nf_files, top_n=5)
            print(f"🛑 Platform Agnostic Logic: {len(nf_files)} files")
            if top_nf:
                print(f"   Primary Sources: {', '.join([f'{d}({c})' for d, c in top_nf])}")
            else:
                print(f"   Primary Sources: None")
            print("   Action: Excluded (Pure business logic/No hardware dependencies).\n")
        
        print("="*70 + "\n")
    
    def filter_files(self, project_files: Dict[str, str]) -> List[str]:
        """
        基于位置的信任策略筛选文件
        
        筛选策略：
        - Rule 1: 核心目录直通（arch/, hal/, bsp/ 等）
        - Rule 2: 宏定义嗅探（平台差异化宏）
        - Rule 3: 汇编直通（asm, __asm__）
        - Rule 4: 驱动层交叉验证（driver/dev/sys 需要 CRITICAL_OPS）
        - Rule 5: 源文件连坐（头文件对应的实现文件）
        
        Args:
            project_files: 文件字典，键为文件路径，值为文件内容
            
        Returns:
            需要保留的文件路径列表
        """
        kept_files = set()  # 使用 set 以便后续连坐策略操作
        
        # 数据结构升级：不仅记录数量，还记录路径分布
        stats = {
            "kept": defaultdict(list),    # key: reason_code, value: list of paths
            "dropped": defaultdict(list)  # key: reason_code, value: list of paths
        }
        
        # 第一轮：基于正则和目录的筛选
        for path, content in project_files.items():
            # Blacklist check first（黑名单优先）
            if self.BLACKLIST_PATTERN.search(path):
                stats["dropped"]["BLACKLIST"].append(path)
                continue
            
            # Rule 1: Location Trust (Blind Trust - 核心目录直通)
            # 这些目录下的文件天生就是架构相关的，即使它只是一行 struct 定义
            if self._is_arch_directory(path):
                kept_files.add(path)
                stats["kept"]["DIR_TRUST"].append(path)
                continue
            
            # Rule 2: Pure ASM (Blind Trust - 汇编直通)
            # 真正的汇编代码，一票通过
            if self.ASM_PATTERN.search(content):
                kept_files.add(path)
                stats["kept"]["ASM_INLINE"].append(path)
                continue
            
            # Rule 3: Platform Macros (Strong Signal - 宏定义嗅探)
            # 条件编译是架构差异最直接的体现
            if self._has_platform_macros(content):
                kept_files.add(path)
                stats["kept"]["MACRO_SENSE"].append(path)
                continue
            
            # Rule 4: Conditional Driver Analysis (驱动层交叉验证)
            # 仅针对 driver/dev/sys 但不在核心目录的文件
            # 必须包含 CRITICAL_OPS (锁, DMA, 中断, 内存操作) 才保留
            # 理由：防止通用的业务驱动（如纯逻辑的 LED 驱动）混入，但保留复杂的 DMA 驱动
            is_driver_context = bool(self.DRIVER_CONTEXT_PATTERN.search(path))
            has_critical_ops = bool(self.CRITICAL_OPS_PATTERN.search(content))
            
            if is_driver_context and has_critical_ops:
                kept_files.add(path)
                stats["kept"]["DRIVER_OPS"].append(path)
                continue
            
            # Drop everything else（其他情况丢弃）
            stats["dropped"]["NO_FEATURE"].append(path)
        
        # 第二轮：源文件连坐 (Source Rescue Strategy)
        # 如果 a.h 在保留列表中，且 a.cpp/a.c 存在于项目中，则强制捞回 a.cpp/a.c
        rescue_files = []
        for file_path in project_files.keys():
            if file_path in kept_files:
                continue
            
            # 检查是否是对应的源文件
            base, ext = os.path.splitext(file_path)
            if ext.lower() in self.SOURCE_EXTENSIONS:
                # 尝试找对应的头文件是否被保留
                # 注意：需要处理路径匹配，通常同目录下同名 .h
                possible_header = base + '.h'
                if possible_header in kept_files:
                    kept_files.add(file_path)
                    rescue_files.append(file_path)
        
        # 记录源文件连坐
        if rescue_files:
            stats["kept"]["SOURCE_RESCUE"] = rescue_files
        
        # 生成专业报告
        total_files = len(project_files)
        kept_count = len(kept_files)
        self._generate_professional_report(total_files, kept_count, stats)
        
        return list(kept_files)

