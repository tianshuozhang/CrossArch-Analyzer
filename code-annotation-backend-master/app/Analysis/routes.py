from app.Analysis import Analysis
from flask import jsonify, request, send_file
import os, sys, zipfile, shutil, json

sys.path.append(os.path.join(os.getcwd(), ".."))


from utils.token import token_required
from utils.file import execute_read_file_data
from utils.path import *
from utils.zip import *
from utils.relation import relations_to_arch_line_relations
from utils.analysis import execute_analysis

from db.db_user import UserDB
from db.db_task import TaskDB
from db.db_relation import RelationDB
from db.db_file import FileDB
from db.db_visualData import VisualizationDataDB

user_db = UserDB()
task_db = TaskDB()
relation_db = RelationDB()
file_db = FileDB()
graph_db = VisualizationDataDB()


@Analysis.route("/progress", methods=["GET"])
@token_required
def get_progress(user_id: int):
    # === 1. 获取任务ID ===
    task_id = request.args.get("task_id")
    task_id = int(task_id)
    # === 2. 获取任务进度 ===
    progress = task_db.get_task_progress(task_id)
    if progress is None:
        return (
            jsonify({"state": "failed", "description": "任务不存在", "rst": None}),
            404,
        )

    # === 3. 返回任务进度 ===
    return (
        jsonify(
            {
                "state": "success",
                "description": "success",
                "rst": {"progress": progress},
            }
        ),
        200,
    )


@Analysis.route("/ask", methods=["POST"])
@token_required
def ask(user_id: int):
    # === 1. 获取用户提问的内容，以及当前打开的文件路径 ===
    question = request.form.get("question")
    if not question:
        return (
            jsonify({"state": "failed", "description": "请提供问题", "rst": None}),
            400,
        )

    opened_file_path = request.form.get("file_path")
    if opened_file_path is None:
        return (
            jsonify(
                {
                    "state": "failed",
                    "description": "请提供当前打开的文件路径，如果没有打开文件，需要提供一个空字串",
                    "rst": None,
                }
            ),
            400,
        )

    # === 2. 获取当前打开的项目路径 ===
    opened_project_id = user_db.get_opened_project_id(user_id)
    if not opened_project_id:
        return (
            jsonify(
                {
                    "state": "failed",
                    "description": "请先打开一个项目",
                    "rst": None,
                }
            ),
            400,
        )

    # === 3. 启动分析任务 ===
    # from LLM.api import orchestrator

    # answer = orchestrator.ask(
    #     question=question, project_root=path_dir_open_content(user_id)
    # )
    answer = None

    # === 4. 答案中，如果graph非空，那么保存graph到打开目录里 ===
    if answer["graph"]:
        graph_id = graph_db.add_visualization_data(
            natural_language_requirement=question,
            title=answer["graph"]["title"],
            project_id=opened_project_id,
        )
        with open(
            path_file_open_graph_item(user_id=user_id, graph_id=graph_id), "w"
        ) as f:
            json.dump(answer["graph"]["option"], f)

    # === 5. 如果打开文件路径不为空，那么读出打开文件的数据 ===
    if opened_file_path:
        try:
            file_data = execute_read_file_data(opened_file_path, user_id)
        except Exception as e:
            return (
                jsonify(
                    {
                        "state": "failed",
                        "description": "读取文件数据失败",
                        "rst": None,
                    }
                ),
                500,
            )
    else:
        file_data = {"file_content": "", "line_arch_tags": ""}
    # === 6. 返回答案 ===
    return jsonify(
        {
            "state": "success",
            "description": "success",
            "rst": {
                "answer": answer["response"],
                "graph": answer["graph"],
                "file_content": file_data["file_content"],
                "line_arch_tags": file_data["line_arch_tags"],
            },
        }
    )


@Analysis.route("/fetch", methods=["GET"])
@token_required
def fetch(user_id: int):
    # === 1. 获取项目ID和任务ID ===
    project_id = request.args.get("project_id")
    if not project_id:
        return (
            jsonify({"state": "failed", "description": "请提供项目ID", "rst": None}),
            400,
        )
    project_id = int(project_id)
    task_id = request.args.get("task_id")
    if not task_id:
        return (
            jsonify({"state": "failed", "description": "请提供任务ID", "rst": None}),
            400,
        )
    task_id = int(task_id)
    cur_open_file_path = request.form.get("file_path")
    if cur_open_file_path is None:
        return (
            jsonify(
                {
                    "state": "failed",
                    "description": "请提供当前打开的文件路径，如果没有打开文件，需要提供一个空字串",
                    "rst": None,
                }
            ),
            400,
        )

    # === 2. 检查任务进度是否为100% ===
    if task_db.get_task_progress(task_id) != 100:
        return (
            jsonify(
                {
                    "state": "failed",
                    "description": "任务未完成，请稍后再试",
                    "rst": {},
                }
            ),
            400,
        )

    # === 3. 取出任务结果，并删除分析目录 ===
    with open(path_file_analysis_task_result(user_id, task_id), "r") as f:
        analysis_result = json.load(f)
    shutil.rmtree(path_dir_analysis_task(user_id, task_id))
    # === 4. 将文件分析报告保存到json里，将架构标记结果记录到数据库里 ===
    with zipfile.ZipFile(
        path_file_save_zip(user_id=user_id, project_id=project_id), "w"
    ) as zip_file:
        report_content = analysis_result["report"]
        zip_file.writestr("report.json", report_content)

    line_arch_dict_list = analysis_result["line_arch_dict_list"]
    for line_arch_dict in line_arch_dict_list:
        file_path = line_arch_dict["file_path"]
        file_id = file_db.get_file_id_by_file_path(file_path)
        if file_id is None:
            return (
                jsonify(
                    {
                        "state": "failed",
                        "description": "分析了不存在的文件",
                        "rst": None,
                    }
                ),
                404,
            )
        relation_db.add_relation(
            start=line_arch_dict["start"],
            end=line_arch_dict["end"],
            arch_names=line_arch_dict["arch_names"],
            project_id=project_id,
            file_id=file_id,
        )
    # === 5. 删除任务 ===
    task_db.delete_task(task_id)
    # === 6. 读取当前打开文件的内容并返回 ===
    opened_project_id = user_db.get_opened_project_id(user_id=user_id)
    if cur_open_file_path == "":
        return (
            jsonify(
                {
                    "state": "success",
                    "description": "success",
                    "rst": {},
                }
            ),
            200,
        )
    else:
        if not opened_project_id:
            return (
                jsonify(
                    {
                        "state": "failed",
                        "description": "只有一个项目被打开时才需要提供一个非空的字符串",
                        "rst": None,
                    }
                ),
                400,
            )
        else:
            try:
                file_data = execute_read_file_data(cur_open_file_path, user_id)
            except:
                return (
                    jsonify(
                        {"state": "failed", "description": "没有找到文件", "rst": None}
                    ),
                    404,
                )
            return (
                jsonify(
                    {
                        "state": "success",
                        "description": "success",
                        "rst": {
                            "file_content": file_data["file_content"],
                            "line_arch_tags": file_data["line_arch_tags"],
                        },
                    }
                ),
                200,
            )


@Analysis.route("/analysis", methods=["POST"])
@token_required
def analysis(user_id: int):
    # === 1. 获取要分析的项目ID ===
    project_id = request.form.get("project_id")
    if not project_id:
        return (
            jsonify({"state": "failed", "description": "请提供项目ID", "rst": None}),
            400,
        )
    project_id = int(project_id)

    # === 2. 将项目复制到analysis目录下，如果是当前项目，就复制，如果是其他项目，就解压 ===
    task_id = task_db.add_task(project_id)
    opened_project_id = user_db.get_opened_project_id(user_id=user_id)
    analysis_project_root = path_dir_analysis_task(user_id, task_id)
    if opened_project_id == project_id:
        shutil.copytree(path_dir_open_content(user_id=user_id), analysis_project_root)
    else:
        zip_extract_file_to(
            src_zip_path=path_file_save_zip(user_id, project_id),
            dst_dir_path=analysis_project_root,
        )

    # === 3. 启动分析任务 ===
    execute_analysis(task_id=task_id, user_id=user_id)

    # === 4. 返回结果 ===
    return (
        jsonify(
            {
                "state": "success",
                "description": "success",
                "rst": {
                    "task_id": task_id,
                },
            }
        ),
        200,
    )


@Analysis.route("/report", methods=["POST"])
@token_required
def report(user_id: int):
    # === 1. 获取要查看的项目ID ===
    project_id = request.form.get("project_id")
    if not project_id:
        return (
            jsonify({"state": "failed", "description": "请提供项目ID", "rst": {}}),
            400,
        )
    project_id = int(project_id)

    # === 2. 获取文字项目报告 ===
    try:
        text_report_content = zip_read_file_from_zip(
            path_file_save_zip(user_id=user_id, project_id=project_id), "report.json"
        )
    except:
        return (
            jsonify(
                {
                    "state": "failed",
                    "description": "没有找到项目报告",
                    "rst": {},
                }
            ),
            404,
        )

    # === 3. 获取架构标注报告 ===
    line_archs_relations = relation_db.get_relations_by_project_id(project_id)
    arch_lines_relations = relations_to_arch_line_relations(line_archs_relations)
    arch_report_content = json.dumps(arch_lines_relations, indent=2)

    # === 4. 拼接报告 ===
    report_content = f"文字分析报告如下：\n{text_report_content}\n架构标注结构化报告如下：\n{arch_report_content}"

    # === 5. 返回项目报告 ===
    return send_file(report_content, download_name="report.txt", as_attachment=True)
