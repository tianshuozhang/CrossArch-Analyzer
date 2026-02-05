from db.db_task import TaskDB

from utils.path import *

import time, json, threading

task_db = TaskDB()

from algo_framework.main import analyze, ask

from llm_tools.task import update_progress


def _all_llm(analysis_project_root: str, task_id: int, result_path: str):
    print(analysis_project_root)
    analysis_result = analyze(
        project_root=analysis_project_root,
        task_id=task_id,
    )
    with open(result_path, "w") as f:
        analysis_result["file_tag_data"] = [
            {
                "file_path": item["file_path"],
                "tag_data": sorted(
                    [
                        {
                            "start": tag_item["start"],
                            "end": tag_item["end"],
                            "arch_names": list(tag_item["arch_names"]),
                        }
                        for tag_item in item["tag_data"]
                    ],
                    key=lambda x: int(x["start"]),
                ),
            }
            for item in analysis_result["file_tag_data"]
        ]
        json.dump(analysis_result, f)

    update_progress(task_id, 100)


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
    project_root = path_dir_analysis_content(user_id, task_id)
    output_path = path_file_analysis_task_result(user_id, task_id)
    threading.Thread(
        target=_all_llm,
        args=(project_root, task_id, output_path),
    ).start()


def execute_ask(question: str, user_id: int):
    answer = ask(question)
    return answer
