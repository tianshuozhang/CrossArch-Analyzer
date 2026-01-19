from app.Analysis import Analysis
from flask import jsonify, request

# from db.db_project import ProjectDB
# from db.db_code import CodeDB
# from db.db_report import ReportDB
# from db.db_user import UserDB
# import rubbish.helper_file as helper_file


# from LLM.api import orchestrator
# import json


# code_DB = CodeDB()
# report_DB = ReportDB()
# project_DB = ProjectDB()
# user_DB = UserDB()

from db.db_task import TaskDB

task_db = TaskDB()


@Analysis.route("/progress", methods=["GET"])
def get_progress():
    # === 1. 获取任务ID ===
    task_id = request.args.get("task_id")

    # === 2. 获取任务进度 ===
    progress = task_db.get_task_progress(task_id)
    if progress == None:
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


# ----------------------------------------------------------------------------------------------------------------------


def get_stats(line_details):
    print("line_details=\n")
    print(line_details)
    counts = {}
    for line_detail in line_details:
        archs = line_detail[2]
        lineLength = line_detail[1][1] - line_detail[1][0] + 1
        for arch in archs:
            if arch not in counts:
                counts[arch] = lineLength
            else:
                counts[arch] += lineLength
    return {
        "funcCount": 0,
        "riscvFuncCount": 0,
        "fileArch": "",
        "counts": counts,
    }


def lineDetails2annotations(line_details):
    annotations = []
    for line_detail in line_details:
        line_range = line_detail[1]
        archs = line_detail[2]
        for line in range(line_range[0], line_range[1] + 1):
            annotations.append(
                {
                    "line": line,
                    "tags": list(archs),
                    "type": "",
                    "fn": "",
                }
            )
    return annotations


@Analysis.route("/analyze", methods=["POST"])
def analyze():
    """用户上传项目，保存项目，并分析项目，将分析结果保存并返回：
    1. 如果之前已上传过该项目，则不保存当前上传的项目；
    2. 如果项目的分析结果已存在，则不会再次分析；"""
    # username = session.get("username")
    # # TMP: 游客模式
    # print("username=" + str(username))
    # if not username:
    #     user_DB.addUser("demo", "123456")
    #     session["username"] = "demo"
    #     username = "demo"
    #     print("username=" + str(session.get("username")))
    # if not username:
    #     return jsonify({"state": "failed", "description": "请先登录", "rst": None})
    username = "demo"
    userId = user_DB.getUserId(username)
    if not userId:
        userId = user_DB.addUser(username, "123456")
    code = request.form.get("code")
    code_name = request.form.get("codeId")
    print(code)
    project_name = code_name
    project_id = project_DB.selectProjectId(userId, project_name)
    if project_id == None:
        # 之前没有上传过该项目，保存现在上传的项目
        codes_num = 1
        file_metadata = {
            code_name: {
                "content": code,
                "file_name": code_name,
                "file_size": len(code),
                "file_type": "cpp",
            }
        }
        # project_zip = request.files.get("project")
        # file_metadata = helper_file.get_metadata_from_zip(project_zip.stream)
        # project_name = project_zip.filename
        # codes_num = sum(1 for meta in file_metadata.values() if meta["file_size"] > 0)
        project_id = project_DB.add_project(
            userId, project_name, helper_file.abs_path(project_name), codes_num
        )
        for file_path, meta in file_metadata.items():
            print(file_path)
            with open(helper_file.abs_path(file_path), "w") as f:
                f.write(meta["content"])
            code_DB.addCode(
                project_id,
                file_path,
                None,
                meta["file_name"],
                meta["file_size"],
                meta["file_type"],
            )
    print(project_id)
    report_path = report_DB.selectReportPath(project_id)
    if report_path == None:
        # 之前没有分析过该项目，现在分析该项目
        # TODO:目前先用project的第一个文件进行分析，因为现在只是单文件的分析
        file_paths = code_DB.selectAllCodes(project_id)
        first_file_path = file_paths[0]
        code = helper_file.load_file(first_file_path)
        print(first_file_path)
        print()
        print(code)
        analysis_result = orchestrator.analyze_code(
            code,
            "请分析以下C/C++代码文件的架构依赖情况，并提供详细的分类报告。",
            first_file_path,
        )
        report_name = project_name + "_report"
        report_path = "report/" + report_name
        helper_file.save_file(report_path, json.dumps(analysis_result))
        report_path = helper_file.abs_path(report_path)
        report_DB.addReport(project_id, report_path)
    with open(report_path, "r") as f:
        analysis_result = json.load(f)
    # TODO:目前只保存第一个文件的parse_result
    code_path = code_DB.selectAllCodes(project_id)[0]
    parse_result_path = code_path.removesuffix(".c") + "_parse_result.json"
    with open(parse_result_path, "w") as f:
        f.write(json.dumps(analysis_result["line_details"]))
    code_DB.modifyCodeParseResult(project_id, code_path, parse_result_path)
    # code_paths = code_DB.selectAllCodes(project_id)
    # for code_path in code_paths:
    #     if code_path:

    annotations = lineDetails2annotations(analysis_result["line_details"])
    status = get_stats(analysis_result["line_details"])
    report = analysis_result["llm_enhanced_analysis"]["natural_language_report"]
    print("status=\n")
    print(status)
    return jsonify(
        {
            "state": "success",
            "description": "分析完成",
            "rst": {
                "reply": "已根据需求完成分类",
                "annotations": annotations,
                "report": report,
                "stats": status,
            },
        }
    )


@Analysis.route("/chat", methods=["POST"])
def chat():
    # project_name = request.form.get("projectname")
    # code_path = request.form.get("codepath")
    code_path = request.form.get("codeId")
    project_name = code_path.split("/")[0]
    prompt = request.form.get("prompt")
    # username = session.get("username")
    # if not username:
    #     return jsonify({"state": "failed", "description": "请先登录", "rst": None})
    username = "demo"
    userId = user_DB.getUserId(username)
    if not userId:
        userId = user_DB.addUser(username, "123456")
    project_id = project_DB.selectProjectId(userId, project_name)
    if not project_id:
        return jsonify({"state": "failed", "description": "项目不存在", "rst": None})
    code_path = code_DB.selectOneCodePath(project_id, code_path)
    analysis_result = orchestrator.analyze(prompt, code_path)
    if analysis_result:
        return jsonify(
            {
                "state": "success",
                "description": "分析完成",
                "rst": analysis_result["llm_enhanced_analysis"][
                    "natural_language_report"
                ],
            }
        )
    else:
        return jsonify({"state": "failed", "description": "分析失败", "rst": None})
