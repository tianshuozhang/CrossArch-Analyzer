import sys
import os

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "LLM"))
sys.path.append(os.path.join(os.getcwd(), "LLM/core"))

from LLM.api import orchestrator

code = """
#include <stdio.h>
// 多架构支持示例
#if !defined(__arm__)
    #define ARCH_NAME \\
        "ARM"
    #define ARCH_FEATURE "NEON"
#elif defined(__x86_64__) 
    #define ARCH_NAME "x86_64" __attribute__((__riscv))
    #define ARCH_FEATURE "SSE/AVX"
#elif defined(__riscv) 
    #define ARCH_NAME "RISC-V" __attribute__((test))
    #define ARCH_FEATURE "V Extension"
#else
    #define ARCH_NAME "Unknown"
    #define ARCH_FEATURE "Generic"
#endif
"""
first_file_path = (
    "/home/yangzheng/CrossArch-Analyzer/code-annotation-backend-master/uploads/hello.c"
)
analysis_result = orchestrator.analyze_code(
    code,
    "请分析以下C/C++代码文件的架构依赖情况，并提供详细的分类报告。",
    first_file_path,
)
print(analysis_result["line_details"])
