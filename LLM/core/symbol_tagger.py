from typing import List, Tuple, Dict
import re
import json
import os

architectures = ["x86", "arm", "riscv", "mips", "powerPC", "loongISA"]


class SymbolTagger:
    def _tag_intrinsics(symbolName: str):
        if any(symbolName.startswith(prefix) for prefix in ["vec_", "vector "]):
            return "powerPC"
        if any(
            symbolName.startswith(prefix)
            for prefix in ["__m", "__lsx_v", "__lasx_xv", "__lasx_xb"]
        ):
            return "loongISA"
        if any(symbolName.startswith(prefix) for prefix in ["__m", "_mm"]):
            return "x86"

        if any(symbolName.startswith(prefix) for prefix in ["__riscv_"]):
            return "riscv"
        if any(
            re.match(pattern, symbolName)
            for pattern in [
                r"v(float|int|uint)(8|16|32|64)mf?[1248]_t",
                r"vbool[2|4|8|16|32|64]_t",
            ]
        ):
            return "riscv"
        if any(
            re.match(pattern, symbolName)
            for pattern in [
                r"v[a-z]+[1-4]?q?_((high|low|lane|laneq|n|high_n)_)?[fsu](8|16|32|64)(_[xfsup](8|16|32|64))?"
            ]
        ):
            return "arm"
        if any(
            re.match(pattern, symbolName)
            for pattern in [
                r"v[a-z]+((8|16|32|64)(ff)?)?(_([vxwmfs]+|vf[24]|xu|rtz|rod))?(_([vxfw]|xu))*_[euif](8|16|32|64)mf?[248](_[ufi](|816|32|64))(x[2-8])?(_m)?",
                r"v[a-z]+_(v|mm|m)_b(1|2|4|8|16|32|64)(_m)?",
            ]
        ):
            return "riscv"
        return "irrelevant"

    def _tag_asm(symbolName: str):
        def _parse_asm_code(asm_code: str):
            parse_result = {"reg": set(), "mem": set(), "opcode": set(), "imm": set()}
            asm_code = asm_code.strip()

            try:
                if " " not in asm_code:
                    if "." in asm_code:
                        parse_result["opcode"].add(".")
                else:
                    opcode = asm_code.split(maxsplit=1)[0].strip()
                    if "." in opcode:
                        parse_result["opcode"].add(".")
                    operand_code = asm_code.split(maxsplit=1)[1].strip()

                    parts = re.split(r"", operand_code)
                    parts = operand_code.split(",")

                    for part in parts:
                        part = part.strip()
                        reg_imms: List[str] = []

                        # 处理内存操作符
                        if "(" in part or ")" in part:
                            parse_result["mem"].add("()")
                            reg_imms += [
                                reg_imm.strip() for reg_imm in re.split(r"[\(\)]", part)
                            ]
                        elif "[" in part or "]" in part:
                            parse_result["mem"].add("[]")
                            reg_imms += [
                                reg_imm.strip() for reg_imm in re.split(r"[\[\]]", part)
                            ]
                        else:
                            reg_imms.append(part)

                        # 处理寄存器和立即数
                        for reg_imm in reg_imms:
                            if reg_imm.startswith("$"):
                                # 确保正则表达式中的 $ 符号被转义
                                if re.match(r"\$[0-9]+", reg_imm):
                                    parse_result["imm"].add("$")
                                elif re.match(r"\$[a-z0-9]+", reg_imm):
                                    parse_result["reg"].add("$")
                                else:
                                    raise NotImplementedError(
                                        f"Unsupported '$' format: {reg_imm}"
                                    )
                            elif reg_imm.startswith("#"):
                                if re.match(r"#[0-9]+", reg_imm):
                                    parse_result["imm"].add("#")
                                else:
                                    raise NotImplementedError(
                                        f"Unsupported '#' format: {reg_imm}"
                                    )
                            elif reg_imm.startswith("%"):
                                # 推荐替换的模式：涵盖 8/16/32/64 位通用寄存器，以及 RIP 和 EFLAGS
                                if re.match(
                                    r"%(r[a-d]x|r[sdi]p|r[sdi]i|r[0-9]{1,2}|e[a-d]x|e[sdi]p|e[sdi]i|[a-d]x|sp|bp|si|di|al|cl|dl|bl|ah|ch|dh|bh|rip|eflags|r?flags)",
                                    reg_imm,
                                    re.IGNORECASE,  # 忽略大小写以处理 %EAX, %eax 等
                                ):
                                    parse_result["reg"].add("x86")
                                elif re.match(r"%r[0-9]{1,2}", reg_imm):
                                    parse_result["reg"].add("%rN")
                                elif re.match(r"%x[0-9]{1,2}", reg_imm):
                                    parse_result["reg"].add("%xN")
                                elif re.match(r"%f[0-9]{1,2}", reg_imm):
                                    parse_result["reg"].add("%fN")
                                elif re.match(r"%v[0-9]{1,2}", reg_imm):
                                    parse_result["reg"].add("%vN")
                                elif re.match(r"%w[0-9]{1,2}", reg_imm):
                                    parse_result["reg"].add("%wN")
                                elif re.match(r"%[0-9]{1,2}", reg_imm):
                                    parse_result["reg"].add("%N")
                                elif re.match(
                                    r"%(zero|ra|sp|tp|a[0-7]|t[0-8]|s[0-9]{1,2})",
                                    reg_imm,
                                ):
                                    parse_result["reg"].add("%ABI")
                                elif re.match(r"%(gp|fp)", reg_imm):
                                    parse_result["reg"].add("riscv")
                                elif re.match(r"%(xzr|wzr)", reg_imm):
                                    parse_result["reg"].add("arm")
                                elif re.match(r"%(ctr|lr)", reg_imm):
                                    parse_result["reg"].add("powerPC")
                                else:
                                    raise NotImplementedError(
                                        f"Unsupported '%' register format: {reg_imm}"
                                    )

            except Exception as e:
                # 捕获任何异常，输出警告信息
                print(
                    f"⚠️ Warning: Failed to fully parse ASM code '{asm_code}'. Error: {type(e).__name__}: {e}"
                )
                # 注意：此处返回部分解析结果 (parse_result)，不会中断程序运行

            return parse_result

        def _classify_asm(parse_result: Dict):
            if any(
                pair[0] in parse_result[pair[1]]
                for pair in [("x86", "reg"), ("$", "imm")]
            ):
                return "x86"
            if any(
                pair[0] in parse_result[pair[1]]
                for pair in [
                    ("[]", "mem"),
                    ("#", "imm"),
                    ("%wN", "reg"),
                    ("arm", "reg"),
                ]
            ):
                return "arm"
            if any(
                pair[0] in parse_result[pair[1]]
                for pair in [("%ABI", "reg"), ("riscv", "reg")]
            ):
                return "riscv"
            if any(pair[0] in parse_result[pair[1]] for pair in [("powerPC", "reg")]):
                return "riscv"
            if "$" in parse_result["reg"] and "." not in parse_result["opcode"]:
                return "mips"
            if "$" in parse_result["reg"] and "." in parse_result["opcode"]:
                return "loongISA"
            return "irrelevant"

        if re.search(r"__?asm\{.*\}", symbolName):
            return "x86"
        m = re.search(r"(asm|__asm__)\(\"(.*)\"\)", symbolName)
        if m:
            symbolName = m.group(1)
        parse_result = _parse_asm_code(symbolName)
        return _classify_asm(parse_result)

    def _tag_macro(symbolName: str, macro_data: Dict):
        for k, v in macro_data.items():
            if symbolName in v:
                return k
        return "irrelevant"

    def _tag_attribute(symbolName: str, attribute_data: Dict):
        m = re.match(r"__attribute__\(\(([^\)]*)\)\)", symbolName)
        if m:
            symbolName = m.group(1)
        for k, v in attribute_data.items():
            if symbolName in v:
                return k
        return "irrelevant"

    def tag(symbols: List[Tuple[str, str]]):
        macro_data = {}
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, "predef_macro.json"), "r") as f:
            macro_data = json.load(f)
        attribute_data = {}
        with open(os.path.join(current_dir, "attributes.json"), "r") as f:
            attribute_data = json.load(f)
        taggedSymbols = {}
        for symbol in symbols:
            symbolName, syntax = symbol
            arch = "irrelevant"
            if syntax in ["function", "type"]:
                arch = SymbolTagger._tag_intrinsics(symbolName)
            elif syntax == "macro":
                arch = SymbolTagger._tag_macro(symbolName, macro_data)
            elif syntax == "asm":
                arch = SymbolTagger._tag_asm(symbolName)
            elif syntax == "attribute":
                arch = SymbolTagger._tag_attribute(symbolName, attribute_data)
            taggedSymbols[symbolName] = arch
        return taggedSymbols
