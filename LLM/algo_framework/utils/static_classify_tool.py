from utils.data_structures import *


def scan_code(code: str) -> TreeSitterOutput:
    pass


def scan_file(file_path: str) -> TreeSitterOutput:
    with open(file_path, "r") as f:
        return scan_code(f.read())
