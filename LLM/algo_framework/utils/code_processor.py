from typing import Tuple, List
import re


class CodeProcessor:
    def remove_regex(code: str, regex: str) -> Tuple[str, List[Tuple[str, int]]]:
        code_ = []
        match_with_line = []
        for ln, line in enumerate(code.splitlines()):
            match = re.search(regex, line)
            while match:
                match_content = match.group()
                match_with_line.append((match_content, ln + 1))
                pos = line.find(match_content)
                left_part = line[:pos]
                right_part = line[pos + len(match_content) :]
                mid_part = ""
                if len(match.groups()) > 0:
                    match_content = match.group(1)
                    pos = line.find(match_content)
                    mid_part = line[pos : pos + len(match_content)]
                line = left_part + mid_part + right_part
                match = re.search(regex, line)
            code_.append(line)
        return "\n".join(code_), match_with_line
