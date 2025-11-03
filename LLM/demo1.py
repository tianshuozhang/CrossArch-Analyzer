#!/usr/bin/env python3
"""
面向多指令集架构的C/C++项目智能代码分类系统 - 独立运行Demo
无需Flask，直接文件运行测试
"""

import os
import sys
from typing import Dict, Any, List
import json

# 添加项目路径到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_environment():
    """设置环境变量和配置"""
    # 设置LLM API配置（根据你的实际API修改）
    os.environ["OPENAI_API_KEY"] = "a21f78197ba7ada844c0479eb42459cf7be1a5cde7b57bc080e1123836654c23"
    os.environ["OPENAI_API_BASE"] = " https://uni-api.cstcloud.cn/v1 "
    
    print("✅ 环境配置完成")

def initialize_components():
    """初始化所有核心组件"""
    print("🔄 初始化组件...")
    
    try:
        
        
        # 1. 初始化智能体
        from agents.orchestrator_agent import OrchestratorAgent
        
        # 2. 配置LLM
        llm_config = {
            "model": "deepseek-v3:671b",
            "openai_api_key": os.environ["OPENAI_API_KEY"],
            "openai_api_base": os.environ["OPENAI_API_BASE"],
            "temperature": 0.2
        }
        
        # 3. 创建智能体实例
        agent = OrchestratorAgent(llm_config)
        
        print("✅ 组件初始化成功")
        return agent
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请检查文件路径和模块名称是否正确")
        return None
    except Exception as e:
        print(f"❌ 初始化错误: {e}")
        return None

def load_test_cases() -> Dict[str, str]:
    """加载测试用例代码"""
    test_cases = {
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
    
    return test_cases

def run_single_analysis(agent, code: str, filename: str):
    """运行单文件分析"""
    print(f"\n{'='*60}")
    print(f"📋 分析文件: {filename}")
    print(f"{'='*60}")
    
    try:
        # 执行代码分析
        print("🔍 正在分析代码架构依赖...")
        result = agent.analyze_code(code, filename)
        
        # 显示分析结果
        display_analysis_result(result)
        
        return result
        
    except Exception as e:
        print(f"❌ 分析过程中出错: {e}")
        return None

def display_analysis_result(result: Dict[str, Any]):
    """美观地显示分析结果"""
    if not result:
        print("⚠️  无分析结果")
        return
    
    # 显示摘要信息
    summary = result.get('summary', {})
    print(f"\n📊 分析摘要:")
    print(f"   文件路径: {summary.get('file_path', 'N/A')}")
    print(f"   总代码行数: {summary.get('total_lines_analyzed', 0)}")
    
    # 显示架构统计
    arch_stats = summary.get('architecture_statistics', {})
    if arch_stats:
        print("   架构分布统计:")
        for arch, count in arch_stats.items():
            print(f"     {arch}: {count} 行")
    
    # 显示详细结果
    detailed_results = result.get('detailed_results', [])
    if detailed_results:
        print(f"\n🔎 详细发现 ({len(detailed_results)} 个架构相关代码块):")
        
        for i, item in enumerate(detailed_results, 1):
            print(f"\n   {i}. 行号: {item.get('line_number', 'N/A')}")
            print(f"      分类: {item.get('category', 'N/A')}")
            print(f"      推理: {item.get('reasoning', 'N/A')}")
            
            evidence = item.get('evidence', [])
            if evidence:
                print(f"      证据: {', '.join(evidence)}")
    else:
        print("\n💡 未发现架构相关代码 - 此文件可能是架构无关的")

def run_batch_analysis(agent, test_cases: Dict[str, str]):
    """运行批量分析"""
    print("\n" + "🚀" + " 开始批量代码分析 " + "🚀")
    print("将分析多种架构的C/C++代码示例")
    
    results = {}
    
    for filename, code in test_cases.items():
        result = run_single_analysis(agent, code, filename)
        results[filename] = result
        
        # 短暂暂停，便于观察
        import time
        time.sleep(1)
    
    return results

def generate_summary_report(results: Dict[str, Any]):
    """生成总结报告"""
    print("\n" + "📈" + " 分析总结报告 " + "📈")
    print("=" * 50)
    
    total_files = len(results)
    files_with_arch_code = 0
    arch_distribution = {}
    
    for filename, result in results.items():
        if result and result.get('detailed_results'):
            files_with_arch_code += 1
            
            # 统计架构分布
            summary = result.get('summary', {})
            arch_stats = summary.get('architecture_statistics', {})
            for arch, count in arch_stats.items():
                arch_distribution[arch] = arch_distribution.get(arch, 0) + 1
    
    print(f"📁 分析文件总数: {total_files}")
    print(f"🔧 包含架构相关代码的文件: {files_with_arch_code}")
    print(f"📄 架构无关文件: {total_files - files_with_arch_code}")
    
    if arch_distribution:
        print("\n🏗️ 检测到的架构类型分布:")
        for arch, count in sorted(arch_distribution.items(), key=lambda x: x[1], reverse=True):
            print(f"   {arch}: {count} 个文件")
    
    # 建议和下一步
    print("\n💡 建议:")
    if files_with_arch_code > 0:
        print("   1. 检查架构相关代码的跨平台兼容性")
        print("   2. 考虑使用条件编译确保多平台支持")
        print("   3. 对架构特定代码进行充分的平台测试")
    else:
        print("   所有分析的文件都是架构无关的，具有良好的可移植性")

def save_results_to_json(results: Dict[str, Any], filename: str = "analysis_results.json"):
    """将结果保存为JSON文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # 确保结果可序列化
            serializable_results = {}
            for key, value in results.items():
                if hasattr(value, '__dict__'):
                    serializable_results[key] = value.__dict__
                else:
                    serializable_results[key] = value
            
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 分析结果已保存到: {filename}")
    except Exception as e:
        print(f"❌ 保存结果失败: {e}")

def main():
    """主函数"""
    print("🎯 面向多指令集架构的C/C++项目智能代码分类系统")
    print("🎯 独立运行演示版")
    print("-" * 60)
    
    # 1. 环境设置
    setup_environment()
    
    # 2. 初始化组件
    agent = initialize_components()
    if not agent:
        print("❌ 初始化失败，程序退出")
        return
    
    # 3. 加载测试用例
    test_cases = load_test_cases()
    print(f"✅ 加载了 {len(test_cases)} 个测试用例")
    
    # 4. 运行分析
    results = run_batch_analysis(agent, test_cases)
    
    # 5. 生成报告
    generate_summary_report(results)
    
    # 6. 保存结果
    save_results_to_json(results,"LLM/analysis_results.json")
    
    print("\n🎉 演示完成!")
    print("💡 你可以修改测试用例或添加自己的C/C++代码进行测试")

if __name__ == "__main__":
    main()
