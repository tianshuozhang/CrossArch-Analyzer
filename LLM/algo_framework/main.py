# from module.prescreener import PreScreener
from module.code_rewriter import CodeRewriter
from module.code_analyzer import CodeAnalyzer
from module.agent import report_Agent

import utils.project_helper as ph
import utils.static_classify_tool as sct
from utils.llm_prompts import system_prompts_for_reporter


def main(
    project_root, user_prompt="请为我分析以下代码的架构依赖关系，并生成一份详细的报告。"
):
    # orig_file_paths, file_paths = PreScreener.prescreen(project_root)
    orig_file_paths = ["testcase.h"]
    file_paths = ["MathFunctions.h"]
    file_tagTarget_relations, advice = CodeRewriter.rewrite(
        file_paths,
        *ph.map_out_tuple(file_paths, sct.scan_file, use_path=True),
    )

    file_analysis_results = CodeAnalyzer.analyze(
        file_paths,
        file_tagTarget_relations,
        *ph.map_out_tuple(file_paths, sct.scan_file, use_path=True),
    )
    file_analysis_results = ph.modify_file_path(
        file_analysis_results, file_paths, orig_file_paths
    )

    report_Agent_instance = report_Agent(system_prompts_for_reporter)

    report = report_Agent_instance.get_response(
        f"请基于以下建议和分析结果，根据用户的要求{user_prompt}，生成一份报告：\n\nllm提出的修改建议：{advice}\n\n分析结果：{file_analysis_results}"
    )

    result = api(file_analysis_results, report)
    import json

    result_data = [
        {
            "file_path": item["file_path"],
            "tag_data": [
                {
                    "start": tag_item["start"],
                    "end": tag_item["end"],
                    "tag_name": list(tag_item["tag_name"]),
                }
                for tag_item in item["tag_data"]
            ],
        }
        for item in result["file_tag_data"]
    ]
    print(json.dumps(result_data, indent=4))

    return result


def api(file_analysis_results, report):
    json_results = {}
    json_results["report"] = report
    json_results["file_tag_data"] = [
        {
            "file_path": k,
            "tag_data": [
                {"start": key[0], "end": key[1], "tag_name": value}
                for key, value in v.items()
            ],
        }
        for k, v in file_analysis_results.data.items()
    ]
    return json_results


if __name__ == "__main__":
    project_root = "LLM/config/eigen"
    main(project_root)
