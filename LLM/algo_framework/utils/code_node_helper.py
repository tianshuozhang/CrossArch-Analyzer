from utils.data_structures import *


def is_tagTarget(code: str):
    return True or False


def is_same_code_node(codeNode1: CodeNode, codeNode2: CodeNode):
    # WARNING: 如果是tagTarget的比较，假设了两个codeNode位于同一文件内
    return codeNode1.name == codeNode2.name and codeNode1.info == codeNode2.info
