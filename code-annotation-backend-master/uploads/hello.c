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
[[no_unique_address]] T payload;
int main() {
    int a = 10;
    printf("Architecture: %s\\n", ARCH_NAME);
    printf("Feature: %s\\n", ARCH_FEATURE);
    
    // 条件编译的不同实现
    #ifdef __arm__
        asm("mov r0, #42");
        _asm("mov r0, #42");
        __asm("mov r0, #42");
    #elif defined(__x86_64__)
        asm("mov $42, %eax");
    #endif
    
    return 0;
}