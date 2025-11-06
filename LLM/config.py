# 指令集架构宏定义数据库
ARCH_MACROS = {
    "ARM": ["__arm__", "__ARM_ARCH", "__aarch64__", "ARM64"],
    "x86": ["__x86_64__", "__i386__", "__i686__", "__x86_64", "_M_X64"],
    "RISC-V": ["__riscv", "__riscv__", "RISCV"],
    "MIPS": ["__mips__", "__mips", "__MIPSEB__", "__MIPSEL__"],
    "PowerPC": ["__powerpc__", "__ppc__", "__PPC__", "_ARCH_PPC"],
    "LoongISA": ["__loongarch__", "__loongarch64", "LOONGARCH"]
}

# 架构相关内置函数映射
INTRINSICS_MAPPING = {
    # x86 SSE/AVX
    "_mm_add_ps": "x86_SSE", "_mm_sub_ps": "x86_SSE",
    "_mm_mul_ps": "x86_SSE", "_mm_add_epi32": "x86_SSE2",
    "_mm256_add_ps": "x86_AVX", "_mm512_load_ps": "x86_AVX512",
    
    # ARM NEON
    "vaddq_f32": "ARM_NEON", "vsubq_f32": "ARM_NEON",
    "vmulq_f32": "ARM_NEON", "vld1q_f32": "ARM_NEON",
    
    # RISC-V Vector
    "__rv_vadd": "RISC-V_V", "__rv_vsub": "RISC-V_V",
    
    # PowerPC AltiVec
    "vec_add": "PowerPC_AltiVec", "vec_sub": "PowerPC_AltiVec"
}

# 内联汇编关键字
INLINE_ASM_KEYWORDS = ["__asm__", "asm", "_asm", "__asm"]

# 测试代码 test_cases 目录
TEST_CASES = {
        "arm_example.c": """
#include <stdio.h>
#include <arm_neon.h>

#ifdef __arm__
    #define ARM_SPECIFIC 1
#else
    #define ARM_SPECIFIC 0
#endif

int main() {
    #ifdef __arm__
        printf("Running on ARM architecture\\n");
        
        // ARM NEON 内联汇编示例
        float32x4_t a = vdupq_n_f32(1.0f);
        float32x4_t b = vdupq_n_f32(2.0f);
        float32x4_t result = vaddq_f32(a, b);
        
        printf("NEON vector addition completed\\n");
    #endif
    
    return 0;
}
        """,
        
        "x86_example.cpp": """
#include <iostream>
#include <xmmintrin.h>

#ifdef __x86_64__
    #define X86_SPECIFIC 1
#else
    #define X86_SPECIFIC 0
#endif

int main() {
    #ifdef __x86_64__
        std::cout << "Running on x86_64 architecture" << std::endl;
        
        // SSE 内置函数示例
        __m128 a = _mm_set_ps(1.0f, 2.0f, 3.0f, 4.0f);
        __m128 b = _mm_set_ps(5.0f, 6.0f, 7.0f, 8.0f);
        __m128 result = _mm_add_ps(a, b);
        
        std::cout << "SSE vector addition completed" << std::endl;
    #endif
    
    // 内联汇编示例
    asm("nop");
    
    return 0;
}
        """,
        
        "multi_arch_example.c": """
#include <stdio.h>

// 多架构支持示例
#if defined(__arm__)
    #define ARCH_NAME "ARM"
    #define ARCH_FEATURE "NEON"
#elif defined(__x86_64__)
    #define ARCH_NAME "x86_64"
    #define ARCH_FEATURE "SSE/AVX"
#elif defined(__riscv)
    #define ARCH_NAME "RISC-V"
    #define ARCH_FEATURE "V Extension"
#else
    #define ARCH_NAME "Unknown"
    #define ARCH_FEATURE "Generic"
#endif

int main() {
    printf("Architecture: %s\\n", ARCH_NAME);
    printf("Feature: %s\\n", ARCH_FEATURE);
    
    // 条件编译的不同实现
    #ifdef __arm__
        asm("mov r0, #42");
    #elif defined(__x86_64__)
        asm("mov $42, %eax");
    #endif
    
    return 0;
}
        """,
        
        "neutral_example.c": """
#include <stdio.h>
#include <stdlib.h>

// 架构无关的纯C代码
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

int main() {
    int number = 5;
    int result = factorial(number);
    
    printf("Factorial of %d is %d\\n", number, result);
    printf("This code is architecture-independent\\n");
    
    return 0;
}
        """
    }
