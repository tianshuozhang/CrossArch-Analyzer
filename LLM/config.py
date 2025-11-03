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
