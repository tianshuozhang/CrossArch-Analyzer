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
    # answer = orchestrator.ask(
    #     question=question, project_root=path_dir_open_content(user_id)
    # )
    return None
