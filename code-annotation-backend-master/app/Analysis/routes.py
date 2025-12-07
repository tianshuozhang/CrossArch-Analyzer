from app.Analysis import Analysis
from flask import jsonify, request
from db.code_db import code_DB
from db.report_db import report_DB
from LLM.api import orchestrator
import json

codeDB = code_DB()
reportDB = report_DB()


def get_stats(line_details):
    counts = {}
    for line_detail in line_details:
        archs = line_detail[2]
        lineLength = line_detail[1][1] - line_detail[1][0]
        for arch in archs:
            if arch == "irrelative":
                arch = "common"
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
    userId = str(request.form.get("userId"))
    codeId = request.form.get("codeId")
    code = request.form.get("code")
    language = request.form.get("language")
    if not userId or not codeId or not code or not language:
        return jsonify({"state": "failed", "description": "参数不完整", "rst": None})
    rst = codeDB.oneUserAddCode(userId, code, codeId, language)
    if rst == "existed":
        return jsonify({"state": "failed", "description": "代码已存在", "rst": None})
    rst = reportDB.selectOneReport(userId, codeId)
    analysis_result = rst
    if analysis_result:
        analysis_result = json.loads(analysis_result)
    else:
        analysis_result = orchestrator.analyze_code(
            code,
            "请分析以下C/C++代码文件的架构依赖情况，并提供详细的分类报告。",
            codeId,
        )
        reportDB.oneUserAddReport(userId, codeId, json.dumps(analysis_result))
    annotations = lineDetails2annotations(analysis_result["line_details"])
    return jsonify(
        {
            "state": "success",
            "description": "分析完成",
            "rst": {
                "reply": "已根据需求完成分类",
                "annotations": annotations,
                "report": analysis_result["llm_enhanced_analysis"][
                    "natural_language_report"
                ],
                "stats": get_stats(analysis_result["line_details"]),
            },
        }
    )


@Analysis.route("/chat", methods=["POST"])
def chat():
    codeId = request.form.get("codeId")
    prompt = request.form.get("prompt")
    analysis_result = orchestrator.analyze(prompt, codeId)
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
