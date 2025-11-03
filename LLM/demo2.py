import os
from agents.enhanced_orchestrator import EnhancedOrchestratorAgent
from agents.specialist_agents import ArchitectureSpecialistAgent, ValidationAgent
from core.communication_bus import CommunicationBus
from utils import setup_environment,load_test_cases,run_batch_analysis,generate_summary_report,save_results_to_json

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
    
def main():
    """主函数"""
    print("🎯 面向多指令集架构的C/C++项目智能代码分类系统")
    print("🎯 独立运行演示版")
    print("-" * 60)

    # 1. 环境设置
    setup_environment()

    # 2. 初始化组件
    orchestrator = initialize_components()
    if not orchestrator:
        print("❌ 初始化失败，程序退出")
        return
    
    # 3. 加载测试用例
    test_cases = load_test_cases()
    print(f"✅ 加载了 {len(test_cases)} 个测试用例")
    # 4. 运行分析
    results = run_batch_analysis(orchestrator, test_cases)
    
    # 5. 生成报告
    generate_summary_report(results)
    
    # 6. 保存结果
    save_results_to_json(results,"LLM/result/demo2.json")

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
