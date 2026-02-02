from utils.data_structures import *
import utils.project_helper as ph
import networkx as nx
from functools import reduce
from utils.symbol_tagger import tag_symbol


class CodeAnalyzer:

    @staticmethod
    def analyze_symbol_relations(
        symbol_relations: list[DepRelation], tagTarget_relations: list[DepRelation]
    ):
        G = nx.DiGraph()
        nodes: dict[str, CodeNode] = {}

        def _prepare():
            for symbol_relation in symbol_relations:
                nodes.setdefault(symbol_relation.node.name, symbol_relation.node)
                for dependency in symbol_relation.dependencies:
                    nodes.setdefault(dependency.name, dependency)
            for tagTarget_relation in tagTarget_relations:
                for dependency in tagTarget_relation.dependencies:
                    nodes.setdefault(dependency.name, dependency)
            for symbol_relation in symbol_relations:
                G.add_edges_from(
                    [
                        (dependence.name, symbol_relation.node.name)
                        for dependence in symbol_relation.dependencies
                    ]
                )

        _prepare()

        top_nodes = [node for node, in_degree in G.in_degree() if in_degree == 0]
        for top_node in top_nodes:
            tag_symbol(nodes[top_node])

        def _broadcast():
            for name in nx.topological_sort(G):
                node = nodes[name]
                for pred_name in G.predecessors(name):
                    pred_node = nodes[pred_name]
                    node.archs |= pred_node.archs

        _broadcast()

    @staticmethod
    def analyze(
        file_paths: list[str],
        file_tagTarget_relations: FileResultDict[list[DepRelation]],
        file_tree_sitter_analysis_result: FileResultDict[TreeSitterAnalysisResult],
        _,
    ) -> FileResultDict[dict[tuple[int, int], set[str]]]:
        
        def merge_tagTarget_relations(args):
            tagTarget_relations, tree_sitter_analysis_result = args
            merged_tagTarget_relations = tree_sitter_analysis_result.tagTarget_relations + tagTarget_relations
            merged_symbol_relations = tree_sitter_analysis_result.symbol_relations
            return merged_tagTarget_relations, merged_symbol_relations

        file_tagTarget_relations, file_symbol_relations = ph.map_out_tuple(
            file_paths,
            merge_tagTarget_relations,
            file_tagTarget_relations,
            file_tree_sitter_analysis_result,
        )
        CodeAnalyzer.analyze_symbol_relations(
            ph.de_file_and_merge(file_symbol_relations),
            ph.de_file_and_merge(file_tagTarget_relations),
        )

        def _make_tagTarget_arch_dict(tagTarget_relation: DepRelation):
            k = (
                tagTarget_relation.node.info.start_line,
                tagTarget_relation.node.info.end_line,
            )
            v = reduce(lambda a, b: a.archs | b.archs, tagTarget_relation.dependencies)
            return {k: v}

        AnalysisResult = ph.map(
            file_paths,
            _make_tagTarget_arch_dict,
            file_tagTarget_relations,
        )

        return AnalysisResult
