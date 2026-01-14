from module.prescreener import PreScreener
from module.code_rewriter import CodeRewriter
from module.code_analyzer import CodeAnalyzer

import utils.project_helper as ph
import utils.static_classify_tool as sct


def main(project_root):
    orig_file_paths, file_paths = PreScreener.prescreen(project_root)
    file_tagTarget_relations = CodeRewriter.rewrite(
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
    return file_analysis_results
