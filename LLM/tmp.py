from algo_framework.module.prescreener import PreScreener
from algo_framework.module.code_rewriter import CodeRewriter
from algo_framework.module.code_analyzer import CodeAnalyzer

import algo_framework.utils.project_helper as ph
import algo_framework.utils.static_classify_tool as sct
from algo_framework.utils.data_structures import *


def main(project_root):
    # orig_file_paths, file_paths = PreScreener.prescreen(project_root)
    orig_file_paths = []
    file_paths = ["PacketMath_corrected.h"]
    # file_tagTarget_relations = CodeRewriter.rewrite(
    #     file_paths,
    #     *ph.map_out_tuple(file_paths, sct.scan_file, use_path=True),
    # )
    file_tagTarget_relations = FileResultDict(data={"PacketMath_corrected.h": []})
    file_analysis_results = CodeAnalyzer.analyze(
        file_paths,
        file_tagTarget_relations,
        *ph.map_out_tuple(file_paths, sct.scan_file, use_path=True),
    )
    return
    file_analysis_results = ph.modify_file_path(
        file_analysis_results, file_paths, orig_file_paths
    )
    return file_analysis_results


if __name__ == "__main__":
    project_root = "LLM/config/eigen"
    main(project_root)
