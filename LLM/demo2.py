import os
import json
from agents.enhanced_orchestrator import EnhancedOrchestratorAgent
from agents.specialist_agents import ArchitectureSpecialistAgent, ValidationAgent
from core.communication_bus import CommunicationBus
from services.build_system_analyzer import BuildSystemAnalyzer
from services.cross_file_correlator import CrossFileCorrelator
from dependency_graph_generator import DependencyGraphGenerator
# from utils import setup_environment,load_test_cases,run_batch_analysis,generate_summary_report,save_results_to_json
from utils import setup_environment, load_test_cases, run_batch_analysis, generate_summary_report

def initialize_components():
    """初始化所有核心组件"""
    print("🔄 初始化组件...")
    try:
        #配置LLM
        llm_config = {
            "model": "deepseek-v3:671b",
            "openai_api_key": os.environ["OPENAI_API_KEY"],
            "openai_api_base": os.environ["OPENAI_API_BASE"],
            "temperature": 0.2
        }
        # 创建主Agent
        orchestrator = EnhancedOrchestratorAgent(llm_config, "main_orchestrator")

        # 创建专业Agent
        arm_specialist = ArchitectureSpecialistAgent("arm_specialist", "ARM")
        validator = ValidationAgent("main_validator")

        # 注册所有Agent到通信总线
        communication_bus = CommunicationBus()
        communication_bus.register_agent(orchestrator.agent_id, orchestrator)
        communication_bus.register_agent(arm_specialist.agent_id, arm_specialist)  
        communication_bus.register_agent(validator.agent_id, validator)

        # 启动通信总线
        communication_bus.start()

        print("✅ 组件初始化成功")
        return orchestrator
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请检查文件路径和模块名称是否正确")
        return None
    except Exception as e:
        print(f"❌ 初始化错误: {e}")
        return None

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
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print("✅ 完整报告保存成功。")
    except Exception as e:
        print(f"❌ 保存完整报告失败: {e}")
        
def main():
    """主函数"""
    print("🎯 面向多指令集架构的C/C++项目智能代码分类系统")
    print("🎯 独立运行演示版")
    print("-" * 60)

    # 1. 环境设置
    setup_environment()
     project_root = "./test_project" # <--- 请将此路径修改为测试项目根目录

    # 2. 初始化组件
    orchestrator = initialize_components()
    if not orchestrator:
        print("❌ 初始化失败，程序退出")
        return
    

    print("\n---[阶段 1]分析项目构建系统 ---")
    build_analyzer = BuildSystemAnalyzer(project_root)
    build_context = build_analyzer.analyze()
    print(f"✅ 构建系统分析完成。")
    print(f"   - 全局宏定义: {build_context.get('definitions', '未找到')}")
    print(f"   - 架构标志: {build_context.get('arch_flags', '未找到')}")


    print("\n--- [阶段 2] 执行逐文件深度分析 ---")
    # 3. 加载测试用例
    test_cases = load_test_cases()
    print(f"✅ 加载了 {len(test_cases)} 个文件进行分析...")

    # 4. 运行分析
    single_file_results = run_batch_analysis(orchestrator, test_cases)
    
    # 5. 生成报告
    generate_summary_report(single_file_results)


    print("\n--- [阶段 3]执行项目级关联分析与可视化数据生成 ---")
    # a. 关联分析，发现深层问题
    print("   - 正在构建全局符号表并查找实现缺失...")
    correlator = CrossFileCorrelator(single_file_results)
    project_issues = correlator.find_missing_implementations()
    generate_project_level_report(project_issues) # 打印项目级风险
    # b. 生成可视化图谱数据
    print("   - 正在生成可视化依赖图谱数据...")
    graph_generator = DependencyGraphGenerator(correlator)
    graph_data = graph_generator.generate_graph_data()
    print("✅ 可视化数据生成完成。")
    
    # 6. 保存结果
    # save_results_to_json(results,"LLM/result/demo2.json")
    full_project_report = {
        "project_name": os.path.basename(project_root),
        "build_context": {k: list(v) for k, v in build_context.items()},
        "single_file_analysis": single_file_results,
        "project_level_issues": project_issues,
        "dependency_graph": graph_data
    }
    save_project_report(full_project_report, "LLM/result/demo2_project_report.json")

    # print("\n" + "-" * 70)
    # print("🎉 增强版演示完成!")
    # print("报告 'demo2_project_report.json' 已生成，其中包含了前端可视化所需的一切数据。")

    # 获取Agent状态
    status = orchestrator.get_agent_status()
    print("Agent状态:", status)

    # 保存状态
    orchestrator.save_agent_state()

    # try:
    #     with open("test_code.cpp", "r") as f:
    #         code_content = f.read()
        
    #     result = orchestrator.analyze_code(code_content, "test_code.cpp")
    #     print("分析结果:", json.dumps(result, indent=2))
        
    #     # 获取Agent状态
    #     status = orchestrator.get_agent_status()
    #     print("Agent状态:", status)
        
    #     # 保存状态
    #     orchestrator.save_agent_state()
        
    # except Exception as e:
    #     print(f"分析错误: {e}")

if __name__ == "__main__":

    main()
