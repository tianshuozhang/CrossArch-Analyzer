#!/usr/bin/env python3
# 测试文件树路径修复

import sys
import os
sys.path.insert(0, '/Users/wangjinyu/Downloads/CrossArch-Analyzer/code-annotation-backend-master')

from utils.project import _make_a_tree, _dict_to_tree

# 模拟 ZIP 文件中的文件列表
namelist = [
    'content/showme.c',
    'content/makefile', 
    'content/triangle.c',
    'content/A.poly',
    'content/tricall.c',
    'content/README',
    'content/triangle.h',
    'graph/'
]

print("原始 namelist:")
for name in namelist:
    print(f"  {name}")

print("\n转换为树结构:")
tree_dict = _make_a_tree(namelist)
print("字典结构:", tree_dict)

print("\n转换为前端格式:")
tree_result = _dict_to_tree(tree_dict)
print("树结构:", tree_result)

# 验证每个节点都有 path 属性
def check_paths(nodes, level=0):
    for node in nodes:
        indent = "  " * level
        print(f"{indent}{node['name']} ({node['type']}) - path: '{node.get('path', 'MISSING')}'")
        if node['children']:
            check_paths(node['children'], level + 1)

print("\n详细检查路径属性:")
check_paths(tree_result)