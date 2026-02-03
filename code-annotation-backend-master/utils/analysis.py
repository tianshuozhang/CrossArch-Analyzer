from db.db_task import TaskDB

from utils.path import *

import time, json, threading

task_db = TaskDB()

import os, sys

sys.path.append(os.path.join(os.getcwd(), ".."))
#     from LLM.api import orchestrator


# def _all_llm(project_root: str, task_id: int, analysis_project_root):

#     analysis_result = orchestrator.analyze(
#         project_root=analysis_project_root,
#         task_id=task_id,
#     )
#     return analysis_result


def _test_long_sleep(task_id: int, output_path: str):
    time.sleep(5)
    result = {"message": "success"}
    task_db.update_progress(task_id, 100)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=4)


def execute_analysis(
    task_id: int,
    user_id: int,
):
    output_path = path_file_analysis_task_result(user_id, task_id)
    threading.Thread(
        target=_test_long_sleep,
        args=(task_id, output_path),
    ).start()


def execute_ask(question: str, user_id: int):
    """执行智能问答，返回对项目架构的分析回答和可视化图数据"""
    import sys
    import os
    
    # 添加LLM模块路径
    llm_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "LLM")
    if llm_path not in sys.path:
        sys.path.insert(0, llm_path)
    
    try:
        from LLM.agents.enhanced_orchestrator import EnhancedOrchestratorAgent
        
        # 创建LLM配置
        llm_config = {
            "model": os.environ.get("MODEL_NAME", "deepseek-v3:671b"),
            "openai_api_key": os.environ.get("OPENAI_API_KEY", "dummy-key"),
            "openai_api_base": os.environ.get("OPENAI_API_BASE", "http://localhost:11434/v1"),
            "temperature": 0.2
        }
        
        # 创建orchestrator实例
        orchestrator = EnhancedOrchestratorAgent(llm_config, "ask_orchestrator")
        
        # 获取项目根目录路径
        project_root = path_dir_open_content(user_id)
        
        # 检查项目是否存在
        if not os.path.exists(project_root):
            return {
                "response": "当前没有打开的项目，无法回答关于项目的问题。",
                "graph": {}
            }
        
        # 构建回答（这里是一个简化的版本，实际实现可能需要调用orchestrator.ask）
        # 由于LLM模块的完整实现比较复杂，我们先返回一个基本的响应
        # 在实际部署时，这里应该调用完整的LLM分析
        
        # 临时实现：返回一个模拟的回答
        # 注意：在完整实现中，应该调用orchestrator.ask方法
        answer = {
            "response": f"关于您的问题：'{question}'，这是一个示例回答。在完整实现中，系统将分析项目结构并提供详细的回答。",
            "graph": {}
        }
        
        return answer
        
    except ImportError as e:
        # 如果导入失败，返回一个错误响应
        return {
            "response": f"抱歉，无法处理您的问题：{str(e)}。LLM模块未正确安装或配置。",
            "graph": {}
        }
    except Exception as e:
        # 处理其他异常
        return {
            "response": f"处理您的问题时出现错误：{str(e)}",
            "graph": {}
        }
