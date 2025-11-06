import os
from typing import Dict, Any
import json
from core.state_manager import AgentStateEncoder
from config import TEST_CASES
def setup_environment():
    """设置环境变量和配置"""
    # 设置LLM API配置（根据你的实际API修改）
    os.environ["OPENAI_API_KEY"] = "a21f78197ba7ada844c0479eb42459cf7be1a5cde7b57bc080e1123836654b23"
    os.environ["OPENAI_API_BASE"] = "https://uni-api.cstcloud.cn/v1"
    
    print("✅ 环境配置完成")
def load_test_cases() -> Dict[str, str]:
    """加载测试用例代码"""
    return TEST_CASES

def run_single_analysis(agent, code: str, filename: str):
    """运行单文件分析"""
    print(f"\n{'='*60}")
    print(f"📋 分析文件: {filename}")
    print(f"{'='*60}")
    print("🔍 正在分析代码架构依赖...")
    result = agent.analyze_code(code, filename)
    print("✅ 分析完成")
    # 显示分析结果
    display_analysis_result(result)
    print(f"{'='*60}\n")
    return result
    # try:
    #     # 执行代码分析
    #     print("🔍 正在分析代码架构依赖...")
    #     result = agent.analyze_code(code, filename)
    #     print("✅ 分析完成")
    #     # 显示分析结果
    #     display_analysis_result(result)
    #     print(f"{'='*60}\n")
    #     return result
        
    # except Exception as e:
    #     print(f"❌ 分析过程中出错: {e}")
    #     return None

def display_analysis_result(result: Dict[str, Any]):
    """美观地显示分析结果"""
    if not result:
        print("⚠️  无分析结果")
        return
    
    # 显示摘要信息
    summary = result.get('summary', {})
    print(f"\n📊 分析摘要:")
    print(f"   文件路径: {result.get('file_path', 'N/A')}")
    print(f"   总代码行数: {summary.get('total_lines_analyzed', 0)}")
    
    # 显示架构统计
    arch_stats = summary.get('architecture_statistics', {})
    if arch_stats:
        print("   架构分布统计:")
        for arch, count in arch_stats.items():
            print(f"     {arch}: {count} 行")
    
    # 显示详细结果
    detailed_results = result.get('line_details', [])
    if detailed_results:
        print(f"\n🔎 详细发现 ({len(detailed_results)} 个架构相关代码块):")
        
        for i, item in enumerate(detailed_results, 1):
            print(f"\n   {i}. 行号: {item.line_number}")
            print(f"      分类: {item.category}")
            print(f"      推理: {item.reasoning}")
            
            evidence = item.evidence
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
            
            json.dump(serializable_results, f, indent=2, ensure_ascii=False,cls=AgentStateEncoder)
        print(f"\n💾 分析结果已保存到: {filename}")
    except Exception as e:
        print(f"❌ 保存结果失败: {e}")

# 新增用于打印项目级风险报告的函数
def generate_project_level_report(issues: list):
    """打印项目级的风险报告"""
    print("\n" + "="*25 + " 项目级风险报告 " + "="*25)
    if not issues:
        print("✅ 未发现项目级的多架构实现缺失问题。")
        return
    
    print(f"⚠️ 发现 {len(issues)} 个潜在的项目级问题：")
    for i, issue in enumerate(issues, 1):
        print(f"\n--- 问题 {i}: {issue['type']} ---")
        print(f"  函数: {issue['function_name']}")
        print(f"  已实现架构: {list(issue['implemented_in'].keys())}")
        print(f"  缺失实现架构: {issue['missing_for_arch']}")
        print(f"  调用位置 (部分): {issue['called_from'][:3]}")
        print(f"  修复建议: {issue['suggestion']}")
    print("="*68)

# 新增用于保存最终完整项目报告的函数
def save_project_report(report_data: dict, output_path: str):
    """将包含所有分析结果的完整项目报告保存为JSON文件"""
    print(f"\n💾 正在保存完整项目报告到: {output_path}")
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False,cls=AgentStateEncoder)
        print("✅ 完整报告保存成功。")
    except Exception as e:
        print(f"❌ 保存完整报告失败: {e}")