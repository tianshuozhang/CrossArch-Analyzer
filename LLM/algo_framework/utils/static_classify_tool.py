from enum import Enum
from typing import Dict, List, Optional, Tuple, Set, NamedTuple
from tree_sitter import Node as TSNode
import sys
sys.path.append('LLM/')

from algo_framework.utils.ts_helper import (
    TSTypes,
    SExpressionTemplate,
    ts_parse,
    findFilteredIdentInTSNode,
    findTSNodesWithSExpr,
    findAncestorUntil,
)
from algo_framework.utils.code_processor import remove_regex


from algo_framework.utils.data_structures import *

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
    UNKNOWN = "unknown"
    OTHER = "other"


class LinkableCodeNode:
    def __init__(
        self,
        text: str,
        nodeType: NodeType,
        define_sentence_tsNodes: List[TSNode] = [],
        info: Optional[TagTargetInfo] = None,
        syntaxType: SyntaxType = SyntaxType.OTHER,
    ):
        self.text = text
        self.linkedCodeNodes: Set["LinkableCodeNode"] = set()
        self.nodeType = nodeType
        self.info = info
        self.define_sentence_tsNodes = define_sentence_tsNodes
        self.syntax = syntaxType

    def linkTo(self, codeNodes: List["LinkableCodeNode"]):
        self.linkedCodeNodes.update(codeNodes)

    def __hash__(self):
        return hash(tuple([self.text] + [n.id for n in self.define_sentence_tsNodes]))

    def __eq__(self, value):
        return isinstance(value, LinkableCodeNode) and (
            self.text == value.text and self.linkedCodeNodes == value.linkedCodeNodes
        )


def _preprocess_code(
    code: str,
) -> Tuple[str, Dict[str, Dict[str, LinkableCodeNode | List[int]]]]:
    # 预处理代码
    # 匹配以下模式，将其从代码中移除并且收集这些符号
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
        code_, expr_lines = remove_regex(code_, pattern)
        exprs = {}
        for expr_line in expr_lines:
            expr_name, line = expr_line
            if expr_name in exprs:
                exprs[expr_name]["lines"].append(line)
            else:
                exprs[expr_name] = {
                    "node": LinkableCodeNode(
                        expr_name, NodeType.OUTERSYMBOL, syntaxType=syntax_type
                    ),
                    "lines": [line],
                }
        collected_exprs[syntax_type] = exprs
    return code_, collected_exprs


def _pack_errors(error_tsNodes: List[TSNode]) -> TreeSitterOutput:
    error_snippets = []
    for errror_tsNode in error_tsNodes:
        content_tsNode = findAncestorUntil(
            errror_tsNode, ["function_definition", "expression_statement"]
        )
        if content_tsNode is None:
            continue
            raise NotImplementedError(f"遇到了没有考虑到的情况：{str(errror_tsNode)}")
        error_snippets.append(
            ErrorSnippet(
                code_content=content_tsNode.text.decode(),
                start_line=content_tsNode.start_point.row + 1,
                end_line=content_tsNode.end_point.row + 1,
            )
        )
    return TreeSitterOutput(
        tree_sitter_analysis_result=None, error_snippets=error_snippets
    )


def _prepare(
    root_tsNode: TSNode,
) -> dict[str | int, LinkableCodeNode]:
    """构建codeNode_graph，它记录了符号名/标记目标的id与codeNode的对应关系"""
    codeNode_graph: Dict[str | int, LinkableCodeNode] = {}

    def _checkSyntaxType(tsNode: TSNode, default: SyntaxType=SyntaxType.MACRO) -> SyntaxType:
            # 将tsNode的节点类型映射到语法类型
            if tsNode.parent.type == TSTypes.CALL_EXPRESSION:
                return SyntaxType.FUNCTION
            if tsNode.type == TSTypes.STRING_CONTENT:
                return SyntaxType.ASM
            if tsNode.type == TSTypes.PRIMITIVE_TYPE:
                return SyntaxType.TYPE
            if tsNode.parent.type == TSTypes.ATTRIBUTE:
                return SyntaxType.ATTRIBUTE
            return default
    def _find_user_define_symbols():
        # 寻找代码的内部符号
        for user_define_sexpr_tuple in SExpressionTemplate.USER_DEFINE_SYMBOL.values():
            # 找内部符号先找定义它的句子
            sentence_tsNodes = findTSNodesWithSExpr(
                root_tsNode, user_define_sexpr_tuple.sentence
            )
            for sentence_tsNode in sentence_tsNodes:
                # 在定义内部符号的句子里找内部符号
                userDefineSymbol_tsNodes = findTSNodesWithSExpr(
                    sentence_tsNode, user_define_sexpr_tuple.define_symbol
                )
                if userDefineSymbol_tsNodes:
                    userDefineSymbol_tsNode = userDefineSymbol_tsNodes[0]
                    symbolName = userDefineSymbol_tsNode.text.decode()
                    # 将符号添加到符号表中
                    if symbolName not in codeNode_graph:
                        codeNode = LinkableCodeNode(
                            text = userDefineSymbol_tsNode.text.decode(),
                            nodeType=NodeType.USERDEFINED,
                            define_sentence_tsNodes=[sentence_tsNode],
                            syntaxType=_checkSyntaxType(userDefineSymbol_tsNode, SyntaxType.UNKNOWN)
                        )
                        codeNode_graph[symbolName] = codeNode
                    else:
                        codeNode_graph[symbolName].define_sentence_tsNodes.append(
                            sentence_tsNode
                        )
                # 定义枚举类型的句子不在考虑范围内
                elif sentence_tsNode.type not in [TSTypes.ENUM_DEF]:
                    continue
                    raise RuntimeError(
                        f"""
    出现了没有考虑到的情况：

        节点内容是：{sentence_tsNode.text.decode()}
        匹配到的句子结构是：{user_define_sexpr_tuple.sentence}
        现在该句子里的匹配方式是：{user_define_sexpr_tuple.define_symbol}
    """
                    )

    def _find_outer_symbols():
        # 寻找代码的外部符号
        outerSymbol_tsNodes = findFilteredIdentInTSNode(root_tsNode)
        outerSymbol_tsNodes += findTSNodesWithSExpr(
            root_tsNode, SExpressionTemplate.TOTAL_SYMBOL
        )        
        for symbol_tsNode in outerSymbol_tsNodes:
            # 将外部符号添加到符号表中
            # 因为已经先添加了内部符号，所以这里不会重复添加错误NodeType的符号
            codeNode = LinkableCodeNode(
                symbol_tsNode.text.decode(),
                NodeType.OUTERSYMBOL,
                syntaxType=_checkSyntaxType(symbol_tsNode),
            )
            codeNode_graph.setdefault(
                symbol_tsNode.text.decode(),
                codeNode,
            )

    def _find_tag_targets():
        # 寻找代码里的标记目标
        tagTarget_tsNodes = findTSNodesWithSExpr(
            root_tsNode, SExpressionTemplate.TAG_TARGET
        )
        for tagTarget_tsNode in tagTarget_tsNodes:
            codeNode = LinkableCodeNode(
                tagTarget_tsNode.text.decode(),
                NodeType.TAGTARGET,
                [tagTarget_tsNode],
                info=TagTargetInfo(
                    start_line=tagTarget_tsNode.start_point.row + 1,
                    end_line=(
                        tagTarget_tsNode.end_point.row
                        if tagTarget_tsNode.text.decode().endswith("\n")
                        else tagTarget_tsNode.end_point.row + 1
                    ),
                ),
            )
            codeNode_graph[tagTarget_tsNode.id] = codeNode

    def _find_others():
        # 寻找代码里的其他内容，这些内容是不需要标记的内容
        # 主要是块的嵌套结构，但是类似内部符号的功能，它们关联了标记目标和外部符号
        other_tsNodes = findTSNodesWithSExpr(root_tsNode, SExpressionTemplate.OTHER)
        for other_tsNode in other_tsNodes:
            codeNode = LinkableCodeNode(other_tsNode.text.decode(), NodeType.OTHER)
            codeNode_graph.setdefault(
                other_tsNode.id,
                codeNode,
            )

    def _checkSenenceCover(codeNode_graph: dict[str | int, LinkableCodeNode]):
        # 检查是否存在未被tagTarget和other覆盖的定义符号的句子
        for code_node in codeNode_graph.values():
            if code_node.nodeType == NodeType.USERDEFINED:
                for sentence_tsNode in code_node.define_sentence_tsNodes:
                    if sentence_tsNode.id not in codeNode_graph:
                        raise RuntimeError(
                            f"""
定义符号的句子没有被tagTarget和other覆盖，该句子是：
{sentence_tsNode.text.decode()}
tagTarget的s表达式为：
{SExpressionTemplate.TAG_TARGET}
other的s表达式为：
{SExpressionTemplate.OTHER}
"""
                        )

    _find_user_define_symbols()
    _find_outer_symbols()
    _find_tag_targets()
    _find_others()
    _checkSenenceCover(codeNode_graph)
    return codeNode_graph


def _linkToOutsideSymbols(
    root_tsNode: TSNode, codeNode_graph: dict[str | int, LinkableCodeNode]
) -> None:
    """将标记目标链接到所在的条件宏里的符号，因为条件宏不是像类等嵌套结构一样具有名字，所以需要单独处理"""
    """方法是找到条件宏节点，然后将条件宏里的有效符号传播到它里面的标记目标"""
    condMacroTSNodes = findTSNodesWithSExpr(root_tsNode, SExpressionTemplate.COND_MACRO)

    def _spread(
        root_tsNode: TSNode, activeSymbolNames: Optional[Set[str]] = None
    ) -> None:
        def _extractActiveSymbols(root: TSNode, active: bool) -> Set[str]:
            extractedSymbolName = set()
            if root.text == "EIGEN_PACKET_MATH_NEON_H".encode():
                pass
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

        # 对于条件宏节点，提取出条件里的有效宏符号，然后将其传播给宏体里的内容
        if activeSymbolNames is None and root_tsNode.type in TSTypes.GROUP_PREPROC_COND:
            cursor = root_tsNode.walk()
            cursor.goto_first_child()
            cursor.goto_next_sibling()
            active = True
            if len(root_tsNode.children) > 1:
                if root_tsNode.children[0].type in TSTypes.GROUP_PREPROC_COND_NEG:
                    active = False
            if active:
                active = root_tsNode.type not in TSTypes.GROUP_PREPROC_COND_NEG
            activeSymbolNames = _extractActiveSymbols(
                cursor.node,
                active
            )
            # 传播给每一个句子
            while cursor.goto_next_sibling():
                if cursor.node.type in TSTypes.GROUP_PREPROC_COND_EL:
                    continue
                _spread(cursor.node, activeSymbolNames)
            cursor.goto_parent()
            return

        # 如果是一个句子（标记目标或其他类型的句子），则将标记目标链接到传播进来的符号
        if root_tsNode.id in codeNode_graph and activeSymbolNames:
            codeNode = codeNode_graph[root_tsNode.id]
            codeNode.linkTo(
                [
                    codeNode_graph[activeSymbolName]
                    for activeSymbolName in activeSymbolNames
                ]
            )
        # 句子还有可能有子句子，所以需要继续传播进去
        cursor = root_tsNode.walk()
        if cursor.goto_first_child():
            _spread(cursor.node, activeSymbolNames)
            while cursor.goto_next_sibling():
                _spread(cursor.node, activeSymbolNames)
            cursor.goto_parent()
            return

    for condMacroTSNode in condMacroTSNodes:
        _spread(condMacroTSNode)


def _makeTagTargetLink(codeNode_graph: dict[str | int, LinkableCodeNode]) -> None:
    # 将标记目标链接到句子里的符号
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


def _makeUserDefinedLink(codeNode_graph: dict[str | int, LinkableCodeNode]) -> None:
    # 将内部符号链接到句子里的内部符号和外部符号
    for code_node in codeNode_graph.values():
        if code_node.nodeType == NodeType.USERDEFINED:
            # 对于定义或生成该内部符号的每一个句子
            for sentence_tsNode in code_node.define_sentence_tsNodes:
                link_symbol_sexpr = SExpressionTemplate.USER_DEFINE_SYMBOL[
                    sentence_tsNode.type
                ].link_symbols
                symbol_tsNodes: List[TSNode] = []
                symbol_codeNodes = []
                # 如果是单个句子（并且不是宏定义句子），那么就直接找内部符号
                if link_symbol_sexpr:
                    symbol_tsNodes = findTSNodesWithSExpr(
                        sentence_tsNode,
                        link_symbol_sexpr,
                    )
                else:
                    # 宏定义句子的处理
                    if sentence_tsNode.type == TSTypes.PREPROC_DEFINE:
                        symbol_tsNodes = findFilteredIdentInTSNode(sentence_tsNode)
                    # 嵌套结构，将该内部符号链接到结构里的每一个子句子
                    else:
                        subTarget_tsNodes = findTSNodesWithSExpr(
                            sentence_tsNode, SExpressionTemplate.TAG_TARGET
                        )
                        for subTarget_tsNode in subTarget_tsNodes:
                            subTarget_codeNode = codeNode_graph[subTarget_tsNode.id]
                            symbol_codeNodes.extend(subTarget_codeNode.linkedCodeNodes)
                # 将找到的每个符号收集起来
                for symbol_tsNode in symbol_tsNodes:
                    symbol_name = symbol_tsNode.text.decode()
                    try:
                        symbol_codeNodes.append(codeNode_graph[symbol_name])
                    except:
                        raise RuntimeError(
                            f"在_prepare中的s表达式没有覆盖符号：{symbol_name}\n所在的句子是：\n{sentence_tsNode.text.decode()}"
                        )
                # 将定义符号的句子所关联的条件宏里的符号也收集进来
                symbol_codeNodes.extend(
                    codeNode_graph[sentence_tsNode.id].linkedCodeNodes
                )
                # 移除自身
                while code_node in symbol_codeNodes:
                    symbol_codeNodes.remove(code_node)
                # 将该内部符号链接到这些收集的符号
                code_node.linkTo(symbol_codeNodes)


def _make_collected_exprs_link(
    codeNode_graph: dict[str | int, LinkableCodeNode],
    collected_exprs: Dict[SyntaxType, Dict],
):
    """将标记目标链接到预处理收集的符号"""

    def _find_tagTarget_include_line(line: int) -> LinkableCodeNode | None:
        for codeNode in codeNode_graph.values():
            if codeNode.nodeType == NodeType.TAGTARGET:
                if codeNode.info.start_line <= line <= codeNode.info.end_line:
                    return codeNode
        return None

    for syntax_type, exprs in collected_exprs.items():
        for expr_name, expr_dict in exprs.items():
            lines = expr_dict["lines"]
            # 找到这些行所在的标记目标，并将该符号
            for line in lines:
                tagTarget_codeNode = _find_tagTarget_include_line(line)
                if tagTarget_codeNode:
                    print(f"链接预处理符号 {expr_name} 到标记目标 {tagTarget_codeNode.text}")
                    # tagTarget_codeNode.linkTo(
                    #     [CodeNode(name=expr_name, syntax=syntax_type)]
                    # )
                    tagTarget_codeNode.linkTo(
                        [LinkableCodeNode(text=expr_name, nodeType=NodeType.OUTERSYMBOL, syntaxType=syntax_type)]
                    )
                    

def _pack_analysis_result(codeNode_graph: dict[str | int, LinkableCodeNode]):
    """把符号表和预处理提取的符号关系整理成关系的输出格式"""
    tagTarget_relations = []
    symbol_relations = []
    for name_or_id, codeNode in codeNode_graph.items():
        # 整理标记目标的关系
        if codeNode.nodeType == NodeType.TAGTARGET:
            dep_relation = DepRelation(
                node=CodeNode(
                    name=f"tagTarget_{name_or_id}",
                    info=codeNode.info,
                ),
                dependencies=[
                    CodeNode(
                        name=linkedCodeNode.text,
                        syntax=codeNode.syntax.value,
                    )
                    for linkedCodeNode in codeNode.linkedCodeNodes
                ],
            )
            tagTarget_relations.append(dep_relation)
        # 整理内部符号的关系
        elif codeNode.nodeType == NodeType.USERDEFINED:
            dep_relation = DepRelation(
                node=CodeNode(name=name_or_id, syntax=codeNode.syntax.value),
                dependencies=[
                    CodeNode(
                        name=linkedCodeNode.text,
                        syntax=codeNode.syntax.value,
                    )
                    for linkedCodeNode in codeNode.linkedCodeNodes
                ],
            )
            symbol_relations.append(dep_relation)

    return TreeSitterOutput(
        tree_sitter_analysis_result=TreeSitterAnalysisResult(
            tagTarget_relations=tagTarget_relations,
            symbol_relations=symbol_relations,
        ),
        error_snippets=[],
    )


def scan_code(code: str) -> TreeSitterOutput:
    import time

    start = time.time()
    code, collected_exprs = _preprocess_code(code)
    print(f"预处理完成, 耗时：{time.time()-start}s")
    root_tsNode, error_tsNodes = ts_parse(code)
    print(f"解析完成, 耗时：{time.time()-start}s")
    if len(error_tsNodes) > 0:
        return _pack_errors(error_tsNodes)
    codeNode_graph = _prepare(root_tsNode)
    print(f"符号表完成, 耗时：{time.time()-start}s")
    _linkToOutsideSymbols(root_tsNode, codeNode_graph)
    print(f"条件宏链接完成, 耗时：{time.time()-start}s")
    _makeTagTargetLink(codeNode_graph)
    print(f"标记目标链接完成, 耗时：{time.time()-start}s")
    _makeUserDefinedLink(codeNode_graph)
    print(f"用户定义符号链接完成, 耗时：{time.time()-start}s")
    _make_collected_exprs_link(codeNode_graph, collected_exprs)
    print(f"预处理符号链接完成, 耗时：{time.time()-start}s")
    result = _pack_analysis_result(codeNode_graph)
    print(f"打包结果完成, 耗时：{time.time()-start}s")
    return result


def scan_file(file_path: tuple[str, ...]) -> TreeSitterOutput:
    with open(file_path, "r", encoding="gbk", errors="ignore") as f:
        return scan_code(f.read())


    
if __name__ == "__main__":
    file_path = "LLM/config/eigen/Eigen/src/Core/arch/NEON/PacketMath.h"
    output = scan_file((file_path,))
    import json

    with open("output.json", "w") as f:
        data = output.tree_sitter_analysis_result
        r1 = data.tagTarget_relations
        r1 = [
            [
                r.node.name,
                [r.node.info.start_line, r.node.info.end_line],
                [dep.name for dep in r.dependencies],
            ]
            for r in r1
        ]
        r2 = data.symbol_relations
        r2 = [
            [r.node.name, r.node.syntax, [dep.name for dep in r.dependencies]]
            for r in r2
        ]
        data = {
            "tagTarget_relations": r1,
            "symbol_relations": r2,
        }
        json.dump(data, f, indent=4)
