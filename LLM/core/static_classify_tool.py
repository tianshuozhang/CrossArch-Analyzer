import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))# 获取当前文件所在目录
LLM_dir = os.path.dirname(current_dir)# 获取LLM目录
sys.path.append(LLM_dir)# 将LLM目录添加到sys.path中

from typing import List, Tuple, Set, Optional, Dict
import json
from enum import Enum

import core.ts_helper as ts_helper
from core.ts_helper import (
    TSTypes,
    SExpressionTemplate,
    findFilteredIdentInTSNode,
    findTSNodesWithSExpr,
)
from tree_sitter import Node as TSNode

from core.code_processor import CodeProcessor


class NodeType(Enum):
    TAGTARGET = "tagtarget"
    USERDEFINED = "userdefined"
    OUTERSYMBOL = "outersymbol"
    OTHER = "other"


class SyntaxType(Enum):
    ASM = "asm"
    TYPE = "type"
    FUNCTION = "function"
    MACRO = "macro"
    ATTRIBUTE = "attribute"
    OTHER = "other"


class CodeNode:
    def __init__(
        self,
        text: str,
        nodeType: NodeType,
        define_sentence_tsNodes: List[TSNode] = [],
        info: Dict = None,
        syntaxType: SyntaxType = SyntaxType.OTHER,
    ):
        self.text = text
        self.linkedCodeNodes = set()
        self.nodeType = nodeType
        self.info = info
        self.define_sentence_tsNodes = define_sentence_tsNodes
        self.syntax = syntaxType

    def linkTo(self, codeNodes: List["CodeNode"]):
        self.linkedCodeNodes.update(codeNodes)

    def __hash__(self):
        return hash(tuple([self.text] + [n.id for n in self.define_sentence_tsNodes]))

    def __eq__(self, value):
        return isinstance(value, CodeNode) and (
            self.text == value.text and self.linkedCodeNodes == value.linkedCodeNodes
        )


class StaticClassifyTool:

    def _preprocess_code(
        code: str,
    ) -> Tuple[str, Dict[str, Dict[str, CodeNode | List[int]]]]:
        pattern_type_args = [
            (r"__attribute__\(\([^\)]*\)\)", SyntaxType.ATTRIBUTE),
            (r"__?asm\{[^\}]*\}", SyntaxType.ASM),
            (
                r"vector +(signed char|unsigned char|signed short|unsigned short|signed int|unsigned int|float|bool char|bool short|bool int|pixel)",
                SyntaxType.TYPE,
            ),
        ]
        collected_exprs = {}
        code_ = code
        for pattern, syntax_type in pattern_type_args:
            code_, expr_lines = CodeProcessor.remove_regex(code_, pattern)
            exprs = {}
            for expr_line in expr_lines:
                expr_name, line = expr_line
                if expr_name in exprs:
                    exprs[expr_name]["lines"].append(line)
                else:
                    exprs[expr_name] = {
                        "node": CodeNode(
                            expr_name, NodeType.OUTERSYMBOL, syntaxType=syntax_type
                        ),
                        "lines": [line],
                    }
            collected_exprs[syntax_type] = exprs
        return code_, collected_exprs

    def _prepare(
        root_tsNode: TSNode,
    ) -> Tuple[dict[str | int, CodeNode], dict[int, CodeNode]]:
        codeNode_graph: Dict[str, CodeNode] = {}
        tsNodeId2CodeNode: Dict[int, CodeNode] = {}
        for user_define_sexpr_tuple in SExpressionTemplate.USER_DEFINE_SYMBOL.values():
            sentence_tsNodes = findTSNodesWithSExpr(
                root_tsNode, user_define_sexpr_tuple.sentence
            )
            for sentence_tsNode in sentence_tsNodes:
                userDefineSymbol_tsNode = findTSNodesWithSExpr(
                    sentence_tsNode, user_define_sexpr_tuple.define_symbol
                )[0]
                symbolName = userDefineSymbol_tsNode.text.decode()
                if symbolName not in codeNode_graph:
                    codeNode = CodeNode(
                        userDefineSymbol_tsNode.text.decode(),
                        NodeType.USERDEFINED,
                        [sentence_tsNode],
                    )
                    codeNode_graph[symbolName] = codeNode
                    tsNodeId2CodeNode.setdefault(
                        sentence_tsNode.id,
                        codeNode,
                    )
                else:
                    codeNode_graph[symbolName].define_sentence_tsNodes.append(
                        sentence_tsNode
                    )
                    tsNodeId2CodeNode.setdefault(
                        sentence_tsNode.id,
                        codeNode_graph[symbolName],
                    )
        outerSymbol_tsNodes = findFilteredIdentInTSNode(root_tsNode)
        outerSymbol_tsNodes += findTSNodesWithSExpr(
            root_tsNode, SExpressionTemplate.TOTAL_SYMBOL
        )

        def _checkSyntaxType(tsNode: TSNode) -> SyntaxType:
            if tsNode.parent.type == TSTypes.CALL_EXPRESSION:
                return SyntaxType.FUNCTION
            if tsNode.type == TSTypes.STRING_CONTENT:
                return SyntaxType.ASM
            if tsNode.type == TSTypes.PRIMITIVE_TYPE:
                return SyntaxType.TYPE
            if tsNode.parent.type == TSTypes.ATTRIBUTE:
                return SyntaxType.ATTRIBUTE
            return SyntaxType.MACRO

        for symbol_tsNode in outerSymbol_tsNodes:
            codeNode = CodeNode(
                symbol_tsNode.text.decode(),
                NodeType.OUTERSYMBOL,
                syntaxType=_checkSyntaxType(symbol_tsNode),
            )
            codeNode_graph.setdefault(
                symbol_tsNode.text.decode(),
                codeNode,
            )
        tagTarget_tsNodes = findTSNodesWithSExpr(
            root_tsNode, SExpressionTemplate.TAG_TARGET
        )
        for tagTarget_tsNode in tagTarget_tsNodes:
            codeNode = CodeNode(
                tagTarget_tsNode.text.decode(),
                NodeType.TAGTARGET,
                [tagTarget_tsNode],
                info={
                    "lineRange": (
                        tagTarget_tsNode.start_point.row + 1,
                        (
                            tagTarget_tsNode.end_point.row
                            if tagTarget_tsNode.text.decode().endswith("\n")
                            else tagTarget_tsNode.end_point.row + 1
                        ),
                    )
                },
            )
            if tagTarget_tsNode.id not in tsNodeId2CodeNode:
                codeNode_graph[tagTarget_tsNode.id] = codeNode
                tsNodeId2CodeNode[tagTarget_tsNode.id] = codeNode
            else:
                codeNode_graph[tagTarget_tsNode.id] = codeNode
        other_tsNodes = findTSNodesWithSExpr(root_tsNode, SExpressionTemplate.OTHER)
        for other_tsNode in other_tsNodes:
            codeNode = CodeNode(other_tsNode.text.decode(), NodeType.OTHER)
            codeNode_graph.setdefault(
                other_tsNode.id,
                codeNode,
            )
        return codeNode_graph, tsNodeId2CodeNode

    def _linkToOutsideSymbols(
        root_tsNode: TSNode, codeNode_graph: dict[str | int, CodeNode]
    ) -> None:
        condMacroTSNodes = findTSNodesWithSExpr(
            root_tsNode, SExpressionTemplate.COND_MACRO
        )

        def _extractActiveSymbols(root: TSNode, active: bool) -> Set[str]:
            extractedSymbolName = set()

            def _walk(root: TSNode, positive: bool) -> None:
                if root.type == TSTypes.UNARY_EXPRESSION:
                    operatorNode = root.child_by_field_name("operator")

                    positive = (
                        not positive
                        if operatorNode and operatorNode.text.decode() == "!"
                        else positive
                    )
                    node = root.child_by_field_name("argument")
                    _walk(node, positive)
                    return

                if root.type == TSTypes.BINARY_EXPRESSION:
                    leftNode = root.child_by_field_name("left")
                    _walk(leftNode, positive)
                    rightNode = root.child_by_field_name("right")
                    _walk(rightNode, positive)
                    return

                if root.type == TSTypes.IDENTIFIER:
                    if positive:
                        extractedSymbolName.add(root.text.decode())
                    return

                cursor = root.walk()
                if cursor.goto_first_child():
                    _walk(cursor.node, positive)
                    while cursor.goto_next_sibling():
                        _walk(cursor.node, positive)
                    cursor.goto_parent()

            _walk(root, active)
            return extractedSymbolName

        def _spread(
            root_tsNode: TSNode, activeSymbolNames: Optional[Set[str]] = None
        ) -> None:
            if (
                activeSymbolNames is None
                and root_tsNode.type in TSTypes.GROUP_PREPROC_COND
            ):
                cursor = root_tsNode.walk()
                cursor.goto_first_child()
                cursor.goto_next_sibling()
                activeSymbolNames = _extractActiveSymbols(
                    cursor.node,
                    root_tsNode.type not in TSTypes.GROUP_PREPROC_COND_NEG,
                )
                while cursor.goto_next_sibling():
                    if cursor.node.type in TSTypes.GROUP_PREPROC_COND_EL:
                        continue
                    _spread(cursor.node, activeSymbolNames)
                cursor.goto_parent()
                return

            if root_tsNode.id in codeNode_graph and activeSymbolNames:
                codeNode = codeNode_graph[root_tsNode.id]
                codeNode.linkTo(
                    [
                        codeNode_graph[activeSymbolName]
                        for activeSymbolName in activeSymbolNames
                    ]
                )

            cursor = root_tsNode.walk()
            if cursor.goto_first_child():
                _spread(cursor.node, activeSymbolNames)
                while cursor.goto_next_sibling():
                    _spread(cursor.node, activeSymbolNames)
                cursor.goto_parent()
                return

        for condMacroTSNode in condMacroTSNodes:
            _spread(condMacroTSNode)

    def _makeTagTargetLink(
        codeNode_graph: dict[str | int, CodeNode],
        tsNodeId2CodeNode: dict[int, CodeNode],
    ) -> None:
        for codeNode in codeNode_graph.values():
            if codeNode.nodeType == NodeType.TAGTARGET:
                tagTarget_tsNode = codeNode.define_sentence_tsNodes[0]
                symbol_tsNodes = findFilteredIdentInTSNode(tagTarget_tsNode)
                symbol_names = [
                    symbol_tsNode.text.decode() for symbol_tsNode in symbol_tsNodes
                ]
                codeNode.linkTo(
                    [codeNode_graph[symbol_name] for symbol_name in symbol_names]
                )

    def _makeUserDefinedLink(
        codeNode_graph: dict[str | int, CodeNode],
        tsNodeId2CodeNode: dict[int, CodeNode],
    ) -> None:
        for code_node in codeNode_graph.values():
            if code_node.nodeType == NodeType.USERDEFINED:
                for sentence_tsNode in code_node.define_sentence_tsNodes:
                    link_symbol_sexpr = SExpressionTemplate.USER_DEFINE_SYMBOL[
                        sentence_tsNode.type
                    ].link_symbols
                    symbol_tsNodes: List[TSNode] = []
                    if link_symbol_sexpr:
                        symbol_tsNodes = findTSNodesWithSExpr(
                            sentence_tsNode,
                            link_symbol_sexpr,
                        )
                    else:
                        if sentence_tsNode.type == TSTypes.PREPROC_DEFINE:
                            symbol_tsNodes = findFilteredIdentInTSNode(sentence_tsNode)
                        else:
                            subTarget_tsNodes = findTSNodesWithSExpr(
                                sentence_tsNode, SExpressionTemplate.TAG_TARGET
                            )
                            for subTarget_tsNode in subTarget_tsNodes:
                                subTarget_codeNode = tsNodeId2CodeNode[
                                    subTarget_tsNode.id
                                ]
                                symbol_codeNodes.extend(
                                    subTarget_codeNode.linkedCodeNodes
                                )
                    symbol_codeNodes = [
                        codeNode_graph[symbol_tsNode.text.decode()]
                        for symbol_tsNode in symbol_tsNodes
                    ]
                    symbol_codeNodes.extend(
                        codeNode_graph[sentence_tsNode.id].linkedCodeNodes
                    )
                    while code_node in symbol_codeNodes:
                        symbol_codeNodes.remove(code_node)
                    code_node.linkTo(symbol_codeNodes)

    def _linkTagTargetWithOuterSymbol(
        codeNode_graph: Dict[str | int, CodeNode],
        collected_exprs: Dict[SyntaxType, Dict],
    ):
        tagTarget_outerSymbol_dict = {}
        outerSymbol_tagTarget_dict = {}
        for key, code_node in codeNode_graph.items():
            if code_node.nodeType == NodeType.TAGTARGET:
                tagTarget_outerSymbol_dict[key] = []
            elif code_node.nodeType == NodeType.OUTERSYMBOL:
                outerSymbol_tagTarget_dict[key] = []

        def _walk(except_ts_id: int, codeNode: CodeNode, path=[]) -> List[CodeNode]:
            if codeNode.nodeType == NodeType.OUTERSYMBOL:
                return [codeNode]
            ret = []
            for linkedNode in codeNode.linkedCodeNodes:
                if linkedNode.text in path:
                    continue
                if any(
                    except_ts_id == tsNode.id
                    for tsNode in linkedNode.define_sentence_tsNodes
                ):
                    continue
                ret += _walk(except_ts_id, linkedNode, path + [codeNode.text])
            return ret

        for tagTarget_tsNode_id in tagTarget_outerSymbol_dict:
            tagTarget_outerSymbol_dict[tagTarget_tsNode_id] = _walk(
                tagTarget_tsNode_id, codeNode_graph[tagTarget_tsNode_id]
            )
        for outerSymbol_tsNode_name in outerSymbol_tagTarget_dict:
            for tagTarget_tsNode_id in tagTarget_outerSymbol_dict:
                if outerSymbol_tsNode_name in [
                    codeNode.text
                    for codeNode in tagTarget_outerSymbol_dict[tagTarget_tsNode_id]
                ]:
                    outerSymbol_tagTarget_dict[outerSymbol_tsNode_name].append(
                        tagTarget_tsNode_id
                    )
        for _, exprs in collected_exprs.items():
            for expr_name in exprs:
                outerSymbol_tagTarget_dict[expr_name] = []
                expr_codeNode = exprs[expr_name]["node"]
                expr_lines = exprs[expr_name]["lines"]
                for tagTarget_tsNode_id in tagTarget_outerSymbol_dict:
                    tagTarget_codeNode = codeNode_graph[tagTarget_tsNode_id]
                    r = tagTarget_codeNode.info["lineRange"]
                    if any(
                        r[0] <= attribute_line <= r[1] for attribute_line in expr_lines
                    ):
                        outerSymbol_tagTarget_dict[expr_name].append(
                            tagTarget_tsNode_id
                        )
                        tagTarget_outerSymbol_dict[tagTarget_tsNode_id].append(
                            expr_codeNode
                        )
        return tagTarget_outerSymbol_dict, outerSymbol_tagTarget_dict

    def _pack_analysis_result(
        tagTarget_outerSymbol_dict: Dict,
        outerSymbol_tagTarget_dict: Dict,
        codeNode_graph: Dict,
        collected_exprs: Dict[SyntaxType, Dict],
    ) -> Dict:
        analysis_result = {
            "symbols": [
                (k, v.syntax.value)
                for k, v in codeNode_graph.items()
                if k in outerSymbol_tagTarget_dict
            ]
            + [
                (expr_name, syntax_type.value)
                for syntax_type in collected_exprs
                for expr_name in collected_exprs[syntax_type]
            ],
            "tagTarget_outerSymbol_dict": {
                (
                    codeNode_graph[k].text,
                    codeNode_graph[k].info["lineRange"],
                ): [vv.text for vv in v]
                for k, v in tagTarget_outerSymbol_dict.items()
            },
            "outerSymbol_tagTarget_dict": {
                k: [
                    (codeNode_graph[vv].text, codeNode_graph[vv].info["lineRange"])
                    for vv in v
                ]
                for k, v in outerSymbol_tagTarget_dict.items()
            },
        }
        return analysis_result

    def scan_code(code: str):
        code, collected_exprs = StaticClassifyTool._preprocess_code(code)
        root_tsNode, error_tsNodes = ts_helper.parse(code)
        if len(error_tsNodes) > 0:
            error_lines = [
                error_tsNode.start_point.row + 1 for error_tsNode in error_tsNodes
            ]
            return None, error_lines
        codeNode_graph, tsNodeId2CodeNode = StaticClassifyTool._prepare(root_tsNode)
        StaticClassifyTool._linkToOutsideSymbols(root_tsNode, codeNode_graph)
        StaticClassifyTool._makeTagTargetLink(codeNode_graph, tsNodeId2CodeNode)
        StaticClassifyTool._makeUserDefinedLink(codeNode_graph, tsNodeId2CodeNode)
        tagTarget_outerSymbol_dict, outerSymbol_tagTarget_dict = (
            StaticClassifyTool._linkTagTargetWithOuterSymbol(
                codeNode_graph, collected_exprs
            )
        )

        analysis_result = StaticClassifyTool._pack_analysis_result(
            tagTarget_outerSymbol_dict,
            outerSymbol_tagTarget_dict,
            codeNode_graph,
            collected_exprs,
        )
        return analysis_result, None


if __name__ == "__main__":
    code = """#include <stdio.h>
// 多架构支持示例
#if !defined(__arm__)
    #define ARCH_NAME \\
        "ARM"
    #define ARCH_FEATURE "NEON"
#elif defined(__x86_64__) 
    #define ARCH_NAME "x86_64" __attribute__((__riscv))
    #define ARCH_FEATURE "SSE/AVX"
#elif defined(__riscv) 
    #define ARCH_NAME "RISC-V" __attribute__((test))
    #define ARCH_FEATURE "V Extension"
#else
    #define ARCH_NAME "Unknown"
    #define ARCH_FEATURE "Generic"
#endif
[[no_unique_address]] T payload;
int main() {
    int a = 10;
    printf("Architecture: %s\\n", ARCH_NAME);
    printf("Feature: %s\\n", ARCH_FEATURE);
    
    // 条件编译的不同实现
    #ifdef __arm__
        asm("mov r0, #42");
        _asm("mov r0, #42");
        __asm("mov r0, #42");
    #elif defined(__x86_64__)
        asm("mov $42, %eax");
    #endif
    
    return 0;
}
    """
    import json

    analysis_result, error_lines = StaticClassifyTool.scan_code(code)
    print(analysis_result.keys())
    print("Symbols:")
    [print("\t" + str(i)) for i in analysis_result["symbols"]]
    print("symbol to tagTarget:")
    print(json.dumps(analysis_result["outerSymbol_tagTarget_dict"], indent=4))
    # if analysis_result:
    #     with open("analysis_result.json", "w") as f:
    #         json.dump(analysis_result["outerSymbol_tagTarget_dict"], f, indent=4)
