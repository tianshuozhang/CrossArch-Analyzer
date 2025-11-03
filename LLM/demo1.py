#!/usr/bin/env python3
"""
面向多指令集架构的C/C++项目智能代码分类系统 - 独立运行Demo
"""

import os
import sys
from utils import setup_environment, load_test_cases, run_batch_analysis, generate_summary_report, save_results_to_json


# 添加项目路径到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


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
    save_results_to_json(results,"LLM/result/demo1.json")
    
    print("\n🎉 演示完成!")
    print("💡 你可以修改测试用例或添加自己的C/C++代码进行测试")

if __name__ == "__main__":
    main()
