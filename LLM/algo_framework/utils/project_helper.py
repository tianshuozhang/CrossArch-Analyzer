import sys
sys.path.append('LLM/')

# from algo_framework.module.code_rewriter import CodeRewriter
from utils.data_structures import *


def _make_map_args(file_path: str, args: tuple):
    args_ = []
    for arg in args:
        if isinstance(arg, FileResultDict):
            try:
                args_.append(arg[file_path])
            except:
                raise KeyError(f"{file_path} 不在 {list(arg.data.keys())}里")
        else:
            args_.append(arg)
    return tuple(args_)


def map(
    file_paths: list[str],
    func,
    *args,
    use_path=False,
) -> FileResultDict:
    fileResultDict = {}
    for file_path in file_paths:
        parsed_args = _make_map_args(file_path, args)
        path_arg = (file_path,) if use_path else ()
        fileResultDict[file_path] = func(path_arg + parsed_args)
    return FileResultDict(data=fileResultDict)


def map_out_tuple(
    file_paths: list[str], func, *args, use_path=False
) -> tuple[list[FileResultDict], ...]:
    fileResultDictTuple = []
    for file_path in file_paths:
        parsed_args = _make_map_args(file_path, args)
        path_arg = (file_path,) if use_path else ()
        
        result_tuple = func(path_arg + parsed_args)
        if not fileResultDictTuple:
            for result in result_tuple:
                fileResultDictTuple.append({file_path: result})
        else:
            for result_i, result in enumerate(result_tuple):
                fileResultDictTuple[result_i][file_path] = result
    return tuple(
        [FileResultDict(data=fileResultDict) for fileResultDict in fileResultDictTuple]
    )


def de_file_and_merge(fileResultDict: FileResultDict) -> list | dict:
    t = type(list(fileResultDict.data.values())[0])
    if t == list:
        return [v for l in fileResultDict.data.values() for v in l]
    elif t == dict:
        return {k: v for d in fileResultDict.data.values() for k, v in d.items()}
    else:
        return [v for v in fileResultDict.data.values()]


def modify_file_path(
    fileResultDict: FileResultDict,
    file_paths_before: list[str],
    file_paths_after: list[str],
) -> FileResultDict[list[str]]:
    fileResultDict_new = {}
    for file_path_before in fileResultDict.data.keys():
        idx = file_paths_before.index(file_path_before)
        fileResultDict_new[file_paths_after[idx]] = fileResultDict[file_path_before]
    return FileResultDict(data=fileResultDict_new)
