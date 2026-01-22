from flask import current_app
import os


def path_dir_user(user_id: int):
    return os.path.join(current_app.config["ROOT"], "data", str(user_id))


#  =======================================================================================================================
def path_dir_open(user_id: int):
    return os.path.join(path_dir_user(user_id), "open")


def path_dir_open_content(user_id: int):
    return os.path.join(path_dir_open(user_id), "content")


def path_dir_open_graph(user_id: int):
    return os.path.join(path_dir_open(user_id), "graph")


def path_file_open_graph_item(user_id: int, graph_id: int):
    return os.path.join(path_dir_open_graph(user_id), f"{graph_id}.json")


def path_file_open_file_abs(user_id: int, rela_file_path: str):
    return os.path.join(path_dir_open_content(user_id), rela_file_path)


# =======================================================================================================================


def path_dir_save(user_id: int):
    return os.path.join(path_dir_user(user_id), "project")


def path_file_save_zip(user_id: int, project_id: int):
    return os.path.join(path_dir_user(user_id), "project", f"{project_id}.zip")


# =======================================================================================================================


def path_dir_extract(user_id: int):
    return os.path.join(path_dir_user(user_id), "extract")


def path_dir_extract_content(user_id: int):
    return os.path.join(path_dir_extract(user_id), "content")


def path_dir_extract_graph(user_id: int):
    return os.path.join(path_dir_extract(user_id), "graph")


# =======================================================================================================================
def path_dir_analysis(user_id: int):
    return os.path.join(path_dir_user(user_id), "analysis")


def path_dir_analysis_task(user_id: int, task_id: int):
    return os.path.join(path_dir_analysis(user_id), f"{task_id}")


def path_file_analysis_task_result(user_id: int, task_id: int):
    return os.path.join(path_dir_analysis_task(user_id, task_id), "result.json")


# =======================================================================================================================


def path_dir_tmp(user_id: int):
    return os.path.join(path_dir_user(user_id), "tmp")


def path_dir_tmp_file(user_id: int, file_id: int):
    return os.path.join(path_dir_tmp(user_id), str(file_id))


# ========================================================================================================================

import shutil


def path_tool_clean_dir(path: str):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def path_tool_basename(path: str):
    basename = os.path.basename(path)
    if basename == "":
        return "dir"
    return basename
