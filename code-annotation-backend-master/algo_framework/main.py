from algo_framework.module.prescreener import PreScreener
from algo_framework.module.code_rewriter import CodeRewriter
from algo_framework.module.code_analyzer import CodeAnalyzer
from algo_framework.module.agent import report_Agent, rewrite_Agent

import algo_framework.utils.project_helper as ph
import algo_framework.utils.static_classify_tool as sct
from algo_framework.utils.llm_prompts import (
    system_prompts_for_reporter,
    system_prompts_for_ask,
)
from algo_framework.utils.global_vars import task_data

from llm_tools.task import check_and_update


def analyze(
    project_root: str,
    task_id,
    user_prompt="请为我分析以下代码的架构依赖关系，并生成一份详细的报告。",
):
    task_data["task_id_saved"] = task_id
    check_and_update(task_id, 1)
    # orig_file_paths, file_paths = PreScreener.prescreen(project_root)
    project_root = project_root.rstrip("/")
    orig_file_paths = [project_root + "/PacketMath.h"]
    file_paths = [project_root + "/PacketMath.h"]
    check_and_update(task_id, 5)
    task_data["task_progress"] = 5
    file_tagTarget_relations, advice = CodeRewriter.rewrite(
        file_paths,
        *ph.map_out_tuple(file_paths, sct.scan_file, use_path=True),
    )
    check_and_update(task_id, 70)
    file_analysis_results = CodeAnalyzer.analyze(
        file_paths,
        file_tagTarget_relations,
        *ph.map_out_tuple(file_paths, sct.scan_file, use_path=True),
    )
    check_and_update(task_id, 80)
    file_analysis_results = ph.modify_file_path(
        file_analysis_results, file_paths, orig_file_paths, project_root
    )

    report_Agent_instance = report_Agent(system_prompts_for_reporter)

    report = report_Agent_instance.get_response(
        f"请基于以下建议和分析结果，根据用户的要求{user_prompt}，生成一份报告：\n\nllm提出的修改建议：{advice}\n\n分析结果：{file_analysis_results}"
    )
    check_and_update(task_id, 95)

    result = api(file_analysis_results, report)

    # import json

    # result_data = [
    #     {
    #         "file_path": item["file_path"],
    #         "tag_data": [
    #             {
    #                 "start": tag_item["start"],
    #                 "end": tag_item["end"],
    #                 "arch_names": list(tag_item["arch_names"]),
    #             }
    #             for tag_item in item["tag_data"]
    #         ],
    #     }
    #     for item in result["file_tag_data"]
    # ]
    # print(json.dumps(result_data, indent=4))

    return result


def ask(question: str):
    agent = rewrite_Agent(system_prompts_for_ask)
    response = agent.get_response(question)
    return {"response": response}


def api(file_analysis_results, report):
    json_results = {}
    json_results["report"] = report
    json_results["file_tag_data"] = [
        {
            "file_path": k,
            "tag_data": [
                {"start": key[0], "end": key[1], "arch_names": value}
                for key, value in v.items()
            ],
        }
        for k, v in file_analysis_results.data.items()
    ]
    return json_results


if __name__ == "__main__":
    project_root = "LLM/config/eigen"
    analyze(project_root)
