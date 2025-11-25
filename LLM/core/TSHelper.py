from tree_sitter import Language, Parser, Node as TSNode, Query, QueryCursor, TreeCursor
import tree_sitter_cpp
from typing import List
from collections import namedtuple

_lang = Language(tree_sitter_cpp.language())
_parser = Parser(_lang)


def parse(code: str) -> TSNode:
    # TODO:修复ERROR节点
    fix_offset = 0
    return _parser.parse(code.encode()).root_node


userDefinedSymbol_s_expr = namedtuple(
    "user_define_s_expr", "sentence, define_symbol, link_symbols"
)


class TSTypes:
    TYPE_SPECIFIER = "type_specifier"
    TYPE_IDENTIFIER = "type_identifier"
    IDENTIFIER = "identifier"
    STRING_CONTENT = "string_content"

    EXPRESSION_STMT = "expression_statement"
    ASM = "gnu_asm_expression"
    UNARY_EXPRESSION = "unary_expression"
    BINARY_EXPRESSION = "binary_expression"
    CALL_EXPRESSION = "call_expression"

    DECLARATION = "declaration"
    PARAMETER_DECLARATION = "parameter_declaration"
    INIT_DECLARATION = "init_declarator"
    POINTER_DECLARATION = "pointer_declarator"
    ARRAY_DECLARATION = "array_declarator"
    FUNCTION_DECLARATION = "function_declarator"

    FUNC_DEF = "function_definition"
    CLASS_DEF = "class_specifier"
    STRUCT_DEF = "struct_specifier"
    UNION_DEF = "union_specifier"
    ENUM_DEF = "enum_specifier"

    USING_TYPE = "alias_declaration"
    TYPEDEF = "type_definition"

    PREPROC_DEFINE = "preproc_def"
    PREPROC_IF = "preproc_if"
    PREPROC_IFDEF = "preproc_ifdef"
    PREPROC_IFNDEF = "#ifndef"
    PREPROC_ELIF = "preproc_elif"
    PREPROC_ELIFDEF = "preproc_elifdef"
    PREPROC_ELIFNDEF = "#elifndef"
    PREPROC_ELSE = "preproc_else"

    GROUP_PREPROC_COND = [
        PREPROC_IF,
        PREPROC_IFDEF,
        PREPROC_IFNDEF,
        PREPROC_ELIF,
        PREPROC_ELIFDEF,
        PREPROC_ELIFNDEF,
    ]

    GROUP_PREPROC_COND_NEG = [
        PREPROC_IFNDEF,
        PREPROC_ELIFNDEF,
    ]

    GROUP_PREPROC_COND_EL = [
        PREPROC_ELIF,
        PREPROC_ELIFDEF,
        PREPROC_ELIFNDEF,
        PREPROC_ELSE,
    ]


class SExpressionTemplate:
    def wrapper(ts_type: str) -> str:
        if ts_type[0] == "#":
            subStr = '"' + ts_type + '"'
        else:
            subStr = f"({ts_type})"
        return f"{subStr} @0"

    def wrapper_with_child(ts_type: str, field: str, child: str) -> str:
        if child[0] == "#":
            subStr = '"' + child + '"'
        else:
            subStr = f"({child})"
        return f"({ts_type} {field}: {subStr} @0)"

    COND_MACRO = " ".join(
        [
            wrapper(TSTypes.PREPROC_IF),
            wrapper(TSTypes.PREPROC_IFDEF),
            wrapper(TSTypes.PREPROC_IFNDEF),
            wrapper(TSTypes.PREPROC_ELIF),
            wrapper(TSTypes.PREPROC_ELIFDEF),
            wrapper(TSTypes.PREPROC_ELIFNDEF),
        ]
    )

    TAG_TARGET = " ".join(
        [
            wrapper(TSTypes.EXPRESSION_STMT),
            wrapper(TSTypes.DECLARATION),
            wrapper(TSTypes.PREPROC_DEFINE),
        ]
    )

    USER_DEFINE_SYMBOL = {
        TSTypes.PREPROC_DEFINE: userDefinedSymbol_s_expr(
            sentence=wrapper(TSTypes.PREPROC_DEFINE),
            define_symbol=" ".join(
                [wrapper_with_child(TSTypes.PREPROC_DEFINE, "name", TSTypes.IDENTIFIER)]
            ),
            link_symbols=None,
        ),
        TSTypes.DECLARATION: userDefinedSymbol_s_expr(
            sentence=wrapper(TSTypes.DECLARATION),
            define_symbol=" ".join(
                [
                    wrapper_with_child(
                        TSTypes.DECLARATION, "declarator", TSTypes.IDENTIFIER
                    ),
                    wrapper_with_child(
                        TSTypes.INIT_DECLARATION, "declarator", TSTypes.IDENTIFIER
                    ),
                    wrapper_with_child(
                        TSTypes.POINTER_DECLARATION, "declarator", TSTypes.IDENTIFIER
                    ),
                    wrapper_with_child(
                        TSTypes.ARRAY_DECLARATION, "declarator", TSTypes.IDENTIFIER
                    ),
                    wrapper_with_child(
                        TSTypes.FUNCTION_DECLARATION, "declarator", TSTypes.IDENTIFIER
                    ),
                ]
            ),
            link_symbols=wrapper_with_child(
                TSTypes.DECLARATION, "type", TSTypes.TYPE_SPECIFIER
            ),
        ),
        TSTypes.USING_TYPE: userDefinedSymbol_s_expr(
            sentence=wrapper(TSTypes.USING_TYPE),
            define_symbol=" ".join(
                [
                    wrapper_with_child(
                        TSTypes.USING_TYPE, "name", TSTypes.TYPE_IDENTIFIER
                    )
                ]
            ),
            link_symbols=None,
        ),
        TSTypes.TYPEDEF: userDefinedSymbol_s_expr(
            sentence=wrapper(TSTypes.TYPEDEF),
            define_symbol=" ".join(
                [
                    wrapper_with_child(
                        TSTypes.TYPEDEF, "declarator", TSTypes.TYPE_IDENTIFIER
                    )
                ]
            ),
            link_symbols=None,
        ),
        TSTypes.FUNC_DEF: userDefinedSymbol_s_expr(
            sentence=wrapper(TSTypes.FUNC_DEF),
            define_symbol=" ".join(
                [
                    wrapper_with_child(
                        TSTypes.FUNCTION_DECLARATION, "declarator", TSTypes.IDENTIFIER
                    )
                ]
            ),
            link_symbols=None,
        ),
        TSTypes.CLASS_DEF: userDefinedSymbol_s_expr(
            sentence=wrapper(TSTypes.CLASS_DEF),
            define_symbol=" ".join(
                [wrapper_with_child(TSTypes.CLASS_DEF, "name", TSTypes.TYPE_IDENTIFIER)]
            ),
            link_symbols=None,
        ),
        TSTypes.STRUCT_DEF: userDefinedSymbol_s_expr(
            sentence=wrapper(TSTypes.STRUCT_DEF),
            define_symbol=" ".join(
                [
                    wrapper_with_child(
                        TSTypes.STRUCT_DEF, "name", TSTypes.TYPE_IDENTIFIER
                    )
                ]
            ),
            link_symbols=None,
        ),
        TSTypes.UNION_DEF: userDefinedSymbol_s_expr(
            sentence=wrapper(TSTypes.UNION_DEF),
            define_symbol=" ".join(
                [wrapper_with_child(TSTypes.UNION_DEF, "name", TSTypes.TYPE_IDENTIFIER)]
            ),
            link_symbols=None,
        ),
        TSTypes.ENUM_DEF: userDefinedSymbol_s_expr(
            sentence=wrapper(TSTypes.ENUM_DEF),
            define_symbol=" ".join(
                [wrapper_with_child(TSTypes.ENUM_DEF, "name", TSTypes.TYPE_IDENTIFIER)]
            ),
            link_symbols=None,
        ),
    }

    OTHER = " ".join(
        [
            wrapper(TSTypes.FUNC_DEF),
            wrapper(TSTypes.CLASS_DEF),
            wrapper(TSTypes.STRUCT_DEF),
            wrapper(TSTypes.UNION_DEF),
            wrapper(TSTypes.ENUM_DEF),
        ]
    )

    RUBBISH_IDENT = wrapper_with_child(
        TSTypes.PARAMETER_DECLARATION, "declarator", TSTypes.IDENTIFIER
    )

    ASM = f"({TSTypes.ASM} assembly_code:(string_literal (string_content) @0))"

    IDENT = wrapper(TSTypes.IDENTIFIER)

    DEFINE = wrapper(TSTypes.PREPROC_DEFINE)

    TOTAL_SYMBOL = " ".join([wrapper(TSTypes.TYPE_SPECIFIER)])


def findTSNodesWithSExpr(ts_node: TSNode, s_expr: str) -> List[TSNode]:
    query = Query(_lang, s_expr)
    queryCursor = QueryCursor(query)
    captures = queryCursor.captures(ts_node)
    return captures.get("0", [])


def _findDefineIdentInTSNode(defineArg_tsNode: TSNode) -> List[TSNode]:
    defineArg_tsNodes = findTSNodesWithSExpr(
        defineArg_tsNode, SExpressionTemplate.DEFINE
    )
    foundIdent_tsNodes = []
    for defineArg_tsNode in defineArg_tsNodes:
        subCode = defineArg_tsNode.child_by_field_name("value").text.decode()
        subRootNode = parse(subCode)
        defineIdent = findTSNodesWithSExpr(subRootNode, SExpressionTemplate.IDENT)
        foundIdent_tsNodes.extend(defineIdent)
    return foundIdent_tsNodes


def findFilteredIdentInTSNode(ts_node: TSNode) -> List[TSNode]:
    defineIdent = _findDefineIdentInTSNode(ts_node)
    idAndASM = findTSNodesWithSExpr(
        ts_node, " ".join([SExpressionTemplate.IDENT, SExpressionTemplate.ASM])
    )
    total_ident = defineIdent + idAndASM
    rubbish = findTSNodesWithSExpr(ts_node, SExpressionTemplate.RUBBISH_IDENT)
    return [n for n in total_ident if n not in rubbish]
