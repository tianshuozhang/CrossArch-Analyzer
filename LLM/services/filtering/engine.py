"""
文件预筛选引擎模块

基于位置的信任策略进行文件筛选，区分核心架构目录和普通驱动目录，
实施差异化的信任策略以平衡筛选精度和覆盖率。

优化版本：支持大型复杂 C++ 项目（如 Linux Kernel、Android）
- 全局源文件关联策略（支持跨目录和模糊匹配）
- 扩展架构感知范围（链接脚本、设备树、独立汇编文件）
- 现代 C++ 并发原语和 SIMD 支持
- 优化正则误报（排除注释行）
"""
import re
import os
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter

from .report_formatter import ScreeningReportFormatter


class FilePreScreener:
    """
    文件预筛选器（优化版）
    
    基于位置的信任策略进行文件筛选，区分核心架构目录和普通驱动目录，
    实施差异化的信任策略。
    
    筛选策略：
        1. 核心目录直通：arch/, hal/, bsp/, platform/ 等目录下的文件直接保留
        2. 宏定义检测：包含平台差异化宏的文件直接保留（排除注释行）
        3. 汇编代码检测：包含 asm/__asm__ 的文件保留
        4. 驱动层交叉验证：driver/dev/sys 路径需要包含关键操作才保留
        5. 全局源文件关联：如果头文件被保留，全局查找对应的源文件（支持模糊匹配）
        6. 构建文件白名单：链接脚本、设备树、独立汇编文件自动保留
    """
    
    # 核心架构目录匹配模式
    ARCH_DIRECTORY_PATTERN = re.compile(
        r"(?i)(arch[/\\]|hal[/\\]|bsp[/\\]|platform[/\\]|mach-|board[/\\])"
    )
    
    # 平台差异化宏匹配模式（优化：排除注释行）
    # 匹配 #ifdef, #if defined, #ifndef
    # 注意：注释排除在 _has_platform_macros 方法中处理
    PLATFORM_MACRO_PATTERN = re.compile(
        r"#\s*(ifdef|if\s+defined|ifndef)\s*"
        r"\(?\s*(ARM|X86|MIPS|RISCV|WIN32|LINUX|APPLE|RTOS|SOC|ARCH|"
        r"__arm__|__x86_64__|__riscv|__mips__|__aarch64__|__powerpc__)",
        re.IGNORECASE
    )
    
    # 汇编代码匹配模式
    ASM_PATTERN = re.compile(r"\b(asm|__asm__)\b")
    
    # 黑名单目录匹配模式
    BLACKLIST_PATTERN = re.compile(
        r"(?i)(test|mock|doc|docs|tools|example|examples|sample|samples|script)"
    )
    
    # 驱动上下文匹配模式
    DRIVER_CONTEXT_PATTERN = re.compile(r"(?i)(driver|dev|sys|module|kernel)")
    
    # 关键操作匹配模式（优化：支持现代 C++ 并发原语和 SIMD）
    # 新增：std::mutex, std::atomic, std::lock_guard, std::unique_lock
    # 新增：SIMD 头文件特征（xmmintrin.h, arm_neon.h 等）
    CRITICAL_OPS_PATTERN = re.compile(
        r"\b("
        r"mutex|spinlock|atomic|dma|phys_|virt_|ioremap|ioctl|interrupt|irq|"
        r"barrier|semaphore|mmap|wmb|rmb|mb|"
        r"std::mutex|std::atomic|std::lock_guard|std::unique_lock|std::shared_mutex|"
        r"std::condition_variable|std::memory_order|"
        r"xmmintrin|emmintrin|pmmintrin|tmmintrin|smmintrin|nmmintrin|wmmintrin|"
        r"immintrin|arm_neon|arm_acle|arm64_neon|"
        r"__m128|__m256|__m512|__mmask|"
        r"vld1q|vst1q|vaddq|vmulq|vshlq"  # ARM NEON intrinsics
        r")\b"
    )
    
    # SIMD 头文件特征模式（检测 #include <xmmintrin.h> 等）
    SIMD_HEADER_PATTERN = re.compile(
        r"#include\s*[<\"](?:"
        r"xmmintrin|emmintrin|pmmintrin|tmmintrin|smmintrin|nmmintrin|wmmintrin|"
        r"immintrin|arm_neon|arm_acle|arm64_neon|"
        r"mmintrin|mm_malloc"
        r")\.h[>\"]"
    )
    
    # 源文件扩展名列表
    SOURCE_EXTENSIONS = ['.c', '.cpp', '.cc', '.cxx']
    
    # 头文件扩展名列表
    HEADER_EXTENSIONS = ['.h', '.hpp', '.hh', '.hxx']
    
    # 构建和底层描述文件扩展名（白名单）
    BUILD_FILE_EXTENSIONS = [
        '.ld',      # 链接脚本
        '.lds',     # 链接脚本（GNU LD）
        '.dts',     # 设备树源文件
        '.dtsi',    # 设备树包含文件
        '.S',       # 汇编源文件（大写，通常需要预处理器）
        '.s',       # 汇编源文件（小写，纯汇编）
    ]
    
    # 构建配置文件名称（白名单，优化：新增）
    # 这些文件对项目构建起决定性作用，应自动保留
    BUILD_CONFIG_NAMES = {
        'CMakeLists.txt',
        'Makefile',
        'Kconfig',
        'Kbuild',
        'Android.bp',
        'Android.mk',
        'meson.build',
        'wscript',
    }
    
    # 测试文件关键词（用于防止过度打捞，优化：新增）
    TEST_FILE_KEYWORDS = {'test', 'mock', 'dummy', 'example', 'sample', 'stub'}
    
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
        
        核心架构目录下的内容默认是架构相关的，即使只是一行结构体定义。
        
        Args:
            path: 文件路径
            
        Returns:
            True 表示是核心架构目录，False 表示不是
        """
        return bool(self.ARCH_DIRECTORY_PATTERN.search(path))
    
    def _has_platform_macros(self, content: str) -> bool:
        """
        检测是否包含平台差异化宏（优化：字符级状态机，解决"字符串陷阱"）
        
        条件编译是架构差异最直接的体现。
        优化：使用字符级状态机准确跟踪代码状态，避免被字符串中的注释符误导。
        
        状态机状态：
            - NORMAL: 正常代码状态
            - IN_STRING_SINGLE: 单引号字符串内
            - IN_STRING_DOUBLE: 双引号字符串内
            - IN_LINE_COMMENT: 单行注释（//）
            - IN_BLOCK_COMMENT: 多行注释（/* ... */）
        
        规则：只有在 NORMAL 状态下扫描到的宏才被视为有效。
        
        Args:
            content: 文件内容
            
        Returns:
            True 表示包含平台差异化宏，False 表示不包含
        """
        # 状态机状态枚举
        STATE_NORMAL = 0
        STATE_IN_STRING_SINGLE = 1  # 单引号字符串 '...'
        STATE_IN_STRING_DOUBLE = 2  # 双引号字符串 "..."
        STATE_IN_LINE_COMMENT = 3   # 单行注释 //
        STATE_IN_BLOCK_COMMENT = 4   # 多行注释 /* ... */
        
        state = STATE_NORMAL
        i = 0
        content_len = len(content)
        
        # 用于构建当前行的宏匹配缓冲区（仅在 NORMAL 状态下）
        macro_buffer = []
        
        while i < content_len:
            char = content[i]
            next_char = content[i + 1] if i + 1 < content_len else None
            
            if state == STATE_NORMAL:
                # 正常代码状态
                if char == "'":
                    # 进入单引号字符串
                    state = STATE_IN_STRING_SINGLE
                    macro_buffer = []  # 清空缓冲区
                elif char == '"':
                    # 进入双引号字符串
                    state = STATE_IN_STRING_DOUBLE
                    macro_buffer = []  # 清空缓冲区
                elif char == '/' and next_char == '/':
                    # 进入单行注释
                    state = STATE_IN_LINE_COMMENT
                    macro_buffer = []  # 清空缓冲区
                    i += 1  # 跳过第二个 '/'
                elif char == '/' and next_char == '*':
                    # 进入多行注释
                    state = STATE_IN_BLOCK_COMMENT
                    macro_buffer = []  # 清空缓冲区
                    i += 1  # 跳过 '*'
                elif char == '#':
                    # 可能是宏定义开始，开始收集字符
                    macro_buffer = ['#']
                elif char == '\n':
                    # 换行，检查缓冲区中是否有宏
                    if macro_buffer:
                        macro_text = ''.join(macro_buffer)
                        if self.PLATFORM_MACRO_PATTERN.search(macro_text):
                            return True
                        macro_buffer = []
                elif macro_buffer:
                    # 继续收集宏字符（直到换行或遇到非宏字符）
                    if char.isspace() or char.isalnum() or char in '()_':
                        macro_buffer.append(char)
                    else:
                        # 遇到非宏字符，检查缓冲区
                        macro_text = ''.join(macro_buffer)
                        if self.PLATFORM_MACRO_PATTERN.search(macro_text):
                            return True
                        macro_buffer = []
            
            elif state == STATE_IN_STRING_SINGLE:
                # 单引号字符串内
                if char == '\\' and next_char:
                    # 转义字符，跳过下一个字符（包括 \'）
                    i += 1
                elif char == "'":
                    # 字符串结束
                    state = STATE_NORMAL
            
            elif state == STATE_IN_STRING_DOUBLE:
                # 双引号字符串内
                if char == '\\' and next_char:
                    # 转义字符，跳过下一个字符（包括 \"）
                    # 注意：\" 不会结束字符串，这是关键优化点
                    i += 1
                elif char == '"':
                    # 字符串结束（只有在非转义的情况下）
                    state = STATE_NORMAL
            
            elif state == STATE_IN_LINE_COMMENT:
                # 单行注释内
                if char == '\n':
                    # 换行结束单行注释
                    state = STATE_NORMAL
            
            elif state == STATE_IN_BLOCK_COMMENT:
                # 多行注释内
                if char == '*' and next_char == '/':
                    # 注释结束
                    state = STATE_NORMAL
                    i += 1  # 跳过 '/'
            
            i += 1
        
        # 文件结束，检查最后的缓冲区
        if state == STATE_NORMAL and macro_buffer:
            macro_text = ''.join(macro_buffer)
            if self.PLATFORM_MACRO_PATTERN.search(macro_text):
                return True
        
        return False
    
    def _is_build_file(self, path: str) -> bool:
        """
        检测是否为构建和底层描述文件
        
        链接脚本、设备树和独立汇编文件都是架构相关的，
        应该自动保留。
        
        Args:
            path: 文件路径
            
        Returns:
            True 表示是构建文件，False 表示不是
        """
        _, ext = os.path.splitext(path)
        return ext.lower() in self.BUILD_FILE_EXTENSIONS
    
    def _has_simd_features(self, content: str) -> bool:
        """
        检测是否包含 SIMD 特征
        
        包括 SIMD 头文件包含和 SIMD 内联函数使用。
        
        Args:
            content: 文件内容
            
        Returns:
            True 表示包含 SIMD 特征，False 表示不包含
        """
        # 检测 SIMD 头文件包含
        if self.SIMD_HEADER_PATTERN.search(content):
            return True
        # 检测 SIMD 内联函数（已在 CRITICAL_OPS_PATTERN 中）
        return bool(self.CRITICAL_OPS_PATTERN.search(content))
    
    def _build_global_file_index(self, project_files: Dict[str, str]) -> Dict[str, List[str]]:
        """
        建立全局文件名索引（优化：支持跨目录和模糊匹配）
        
        为所有文件建立基于文件名的索引，用于全局源文件关联策略。
        索引键为文件名（不含路径和扩展名），值为文件路径列表。
        
        例如：
            - include/driver.h -> {'driver': ['include/driver.h']}
            - src/driver.cpp -> {'driver': ['src/driver.cpp']}
            - src/driver_impl.cpp -> {'driver_impl': ['src/driver_impl.cpp'], 
                                      'driver': ['src/driver_impl.cpp']}  # 模糊匹配
        
        Args:
            project_files: 文件字典，键为文件路径，值为文件内容
            
        Returns:
            文件名索引字典，键为文件名（不含扩展名），值为文件路径列表
        """
        index: Dict[str, List[str]] = defaultdict(list)
        
        for file_path in project_files.keys():
            # 获取文件名（不含路径）
            basename = os.path.basename(file_path)
            # 获取文件名（不含扩展名）
            name_without_ext, _ = os.path.splitext(basename)
            
            # 添加到索引
            index[name_without_ext].append(file_path)
            
            # 模糊匹配：如果文件名包含下划线分隔的后缀（如 driver_impl），
            # 也将其基础部分加入索引（如 driver_impl -> driver）
            # 这样可以匹配 driver.h -> driver_impl.cpp
            if '_' in name_without_ext:
                base_name = name_without_ext.split('_')[0]
                if base_name and len(base_name) >= 3:  # 避免过短的匹配
                    index[base_name].append(file_path)
        
        return dict(index)
    
    def _find_matching_sources_global(
        self, 
        header_path: str, 
        file_index: Dict[str, List[str]],
        all_files: Dict[str, str]
    ) -> List[str]:
        """
        全局查找与头文件匹配的源文件（优化：支持跨目录和模糊匹配，防止过度打捞）
        
        如果 include/driver.h 被保留，那么项目任意深度的：
            - src/driver.cpp
            - src/driver_impl.cpp
            - libs/driver/src.cpp
        都应该被"打捞"回来。
        
        优化：增加二级过滤逻辑，防止误打捞测试文件（如 driver_test.cpp）。
        
        Args:
            header_path: 头文件路径
            file_index: 全局文件名索引
            all_files: 所有文件字典
            
        Returns:
            匹配的源文件路径列表
        """
        # 获取头文件名（不含扩展名）
        basename = os.path.basename(header_path)
        header_name, _ = os.path.splitext(basename)
        
        matching_sources = []
        
        def _is_test_file(candidate_path: str) -> bool:
            """
            检查文件是否为测试文件（优化：防止过度打捞）
            
            如果文件名包含测试关键词（test, mock, dummy, example 等），
            且不在核心架构目录中，则视为测试文件，拒绝打捞。
            
            Args:
                candidate_path: 候选文件路径
                
            Returns:
                True 表示是测试文件，False 表示不是
            """
            # 获取文件名（不含路径和扩展名）
            candidate_basename = os.path.basename(candidate_path)
            candidate_name, _ = os.path.splitext(candidate_basename)
            candidate_name_lower = candidate_name.lower()
            
            # 检查是否包含测试关键词
            for keyword in self.TEST_FILE_KEYWORDS:
                if keyword in candidate_name_lower:
                    # 如果不在核心架构目录中，则视为测试文件
                    if not self._is_arch_directory(candidate_path):
                        return True
            return False
        
        # 精确匹配：查找同名源文件
        if header_name in file_index:
            for candidate_path in file_index[header_name]:
                # 确保是源文件且不是头文件本身
                _, ext = os.path.splitext(candidate_path)
                if (ext.lower() in self.SOURCE_EXTENSIONS and 
                    candidate_path != header_path and
                    candidate_path in all_files):
                    # 二级过滤：排除测试文件
                    if not _is_test_file(candidate_path):
                        matching_sources.append(candidate_path)
        
        # 模糊匹配：查找包含头文件名作为前缀的源文件
        # 例如 driver.h -> driver_impl.cpp, driver_linux.cpp
        for candidate_name, candidate_paths in file_index.items():
            # 检查是否以头文件名开头（支持后缀变体）
            if candidate_name.startswith(header_name + '_') or \
               (header_name in candidate_name and len(candidate_name) > len(header_name)):
                for candidate_path in candidate_paths:
                    _, ext = os.path.splitext(candidate_path)
                    if (ext.lower() in self.SOURCE_EXTENSIONS and
                        candidate_path != header_path and
                        candidate_path in all_files and
                        candidate_path not in matching_sources):
                        # 二级过滤：排除测试文件
                        if not _is_test_file(candidate_path):
                            matching_sources.append(candidate_path)
        
        return matching_sources
    
    def _get_top_dirs(self, file_list: List[str], top_n: int = 3) -> List[tuple]:
        """
        从文件列表中提取出现频率最高的相对目录
        
        自动去除公共前缀，只显示有意义的子目录。
        
        Args:
            file_list: 文件路径列表
            top_n: 返回前 N 个目录
            
        Returns:
            目录及其出现次数的元组列表，按频率降序排列
        """
        if not file_list:
            return []

        # 尝试找到所有文件的公共根目录
        try:
            # os.path.commonpath 可能会抛出异常（如果路径混合了不同驱动器）
            common_root = os.path.commonpath(file_list)
            
            # 如果 common_root 本身就是一个文件（单一文件情况），取其目录
            if os.path.isfile(common_root):
                common_root = os.path.dirname(common_root)
        except ValueError:
            common_root = ""

        # 计算相对路径并提取有意义的层级
        meaningful_dirs = []
        for f in file_list:
            try:
                # 获取相对路径
                if common_root:
                    rel_path = os.path.relpath(f, start=common_root)
                else:
                    rel_path = f
                
                # 提取目录部分
                d = os.path.dirname(rel_path)
                
                # 标准化分隔符
                d = d.replace("\\", "/")
                
                # 如果是根目录，标记为 Root
                if d == "." or d == "":
                    meaningful_dirs.append("[Root]")
                    continue

                # 提取前两级目录以避免过长
                parts = d.split("/")
                if len(parts) > 2:
                    simplified = f"{parts[0]}/{parts[1]}"
                    meaningful_dirs.append(simplified)
                else:
                    meaningful_dirs.append(d)

            except Exception:
                # 如果相对路径计算失败，回退到目录名
                meaningful_dirs.append(os.path.dirname(f))

        return Counter(meaningful_dirs).most_common(top_n)
    
    def _generate_professional_report(self, total: int, kept: int, stats: Dict) -> None:
        """
        生成并打印架构预筛选报告
        
        Args:
            total: 总文件数
            kept: 保留文件数
            stats: 统计字典，包含 kept 和 dropped 两个子字典
        """
        dropped = total - kept
        filter_rate = (dropped / total * 100) if total > 0 else 0
        
        formatter = ScreeningReportFormatter()
        lines = []
        
        # 1. 执行摘要
        lines.extend(formatter.format_summary(total, kept, filter_rate))
        
        # 2. 保留策略分析
        lines.extend(formatter.format_retention_analysis(stats, self._get_top_dirs))
        
        # 3. 噪声组件分析
        lines.extend(formatter.format_noise_analysis(stats, self._get_top_dirs))
        
        # 打印报告
        formatter.print_report(lines)
    
    def filter_files(self, project_files: Dict[str, str]) -> List[str]:
        """
        基于位置的信任策略筛选文件（优化版 V2.1）
        
        筛选策略：
            0. 构建配置文件白名单：CMakeLists.txt, Makefile, Kconfig 等自动保留
            1. 构建文件白名单：链接脚本、设备树、独立汇编文件自动保留
            2. 核心目录直通：arch/, hal/, bsp/ 等目录下的文件直接保留
            3. 汇编代码检测：包含 asm, __asm__ 的文件保留
            4. 宏定义检测：包含平台差异化宏的文件直接保留（字符级状态机，解决"字符串陷阱"）
            5. SIMD 特征检测：包含 SIMD 头文件或内联函数的文件保留
            6. 驱动层交叉验证：driver/dev/sys 路径需要包含关键操作才保留
            7. 全局源文件关联：如果头文件被保留，全局查找对应的源文件（支持模糊匹配，防止过度打捞）
        
        Args:
            project_files: 文件字典，键为文件路径，值为文件内容
            
        Returns:
            需要保留的文件路径列表
        """
        kept_files = set()
        
        # 统计数据结构：记录保留和丢弃的文件及其原因
        stats = {
            "kept": defaultdict(list),    # key: reason_code, value: list of paths
            "dropped": defaultdict(list)   # key: reason_code, value: list of paths
        }
        
        # 第一轮：基于正则和目录的筛选
        for path, content in project_files.items():
            # 黑名单检查优先
            if self.BLACKLIST_PATTERN.search(path):
                stats["dropped"]["BLACKLIST"].append(path)
                continue
            
            # 规则0：构建配置文件白名单（优化：新增，优先检查）
            # 检查文件名是否全字匹配构建配置文件名
            # 这些文件对项目构建起决定性作用，应自动保留
            basename = os.path.basename(path)
            if basename in self.BUILD_CONFIG_NAMES:
                kept_files.add(path)
                stats["kept"]["BUILD_CONFIG"].append(path)
                continue
            
            # 规则1：构建文件白名单（扩展名检查）
            # 链接脚本、设备树和独立汇编文件都是架构相关的，自动保留
            if self._is_build_file(path):
                kept_files.add(path)
                stats["kept"]["BUILD_FILE"].append(path)
                continue
            
            # 规则2：核心目录直通
            # 这些目录下的文件默认是架构相关的
            if self._is_arch_directory(path):
                kept_files.add(path)
                stats["kept"]["DIR_TRUST"].append(path)
                continue
            
            # 规则3：汇编代码检测
            if self.ASM_PATTERN.search(content):
                kept_files.add(path)
                stats["kept"]["ASM_INLINE"].append(path)
                continue
            
            # 规则4：平台宏检测（优化：字符级状态机，解决"字符串陷阱"）
            # 条件编译是架构差异最直接的体现
            if self._has_platform_macros(content):
                kept_files.add(path)
                stats["kept"]["MACRO_SENSE"].append(path)
                continue
            
            # 规则5：SIMD 特征检测（优化：新增）
            # SIMD 指令是架构相关的硬件特性
            if self._has_simd_features(content):
                kept_files.add(path)
                stats["kept"]["SIMD_FEATURE"].append(path)
                continue
            
            # 规则6：驱动层交叉验证（优化：支持现代 C++ 并发原语）
            # 仅针对 driver/dev/sys 但不在核心目录的文件
            # 必须包含关键操作（锁、DMA、中断、内存操作、现代 C++ 并发原语）才保留
            # 防止通用的业务驱动（如纯逻辑的 LED 驱动）混入，但保留复杂的 DMA 驱动
            is_driver_context = bool(self.DRIVER_CONTEXT_PATTERN.search(path))
            has_critical_ops = bool(self.CRITICAL_OPS_PATTERN.search(content))
            
            if is_driver_context and has_critical_ops:
                kept_files.add(path)
                stats["kept"]["DRIVER_OPS"].append(path)
                continue
            
            # 其他情况丢弃
            stats["dropped"]["NO_FEATURE"].append(path)
        
        # 第二轮：全局源文件关联策略（优化：支持跨目录和模糊匹配）
        # 建立全局文件名索引
        file_index = self._build_global_file_index(project_files)
        
        # 查找所有被保留的头文件
        kept_headers = [
            path for path in kept_files 
            if os.path.splitext(path)[1].lower() in self.HEADER_EXTENSIONS
        ]
        
        # 为每个保留的头文件查找匹配的源文件
        rescue_files = []
        for header_path in kept_headers:
            matching_sources = self._find_matching_sources_global(
                header_path, file_index, project_files
            )
            
            for source_path in matching_sources:
                if source_path not in kept_files:
                    kept_files.add(source_path)
                    rescue_files.append(source_path)
        
        # 记录源文件关联
        if rescue_files:
            stats["kept"]["SOURCE_RESCUE"] = rescue_files
        
        # 生成报告
        total_files = len(project_files)
        kept_count = len(kept_files)
        self._generate_professional_report(total_files, kept_count, stats)
        
        return list(kept_files)

