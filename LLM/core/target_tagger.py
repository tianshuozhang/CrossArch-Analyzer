from typing import Dict, List, Tuple


class TargetTagger:
    def tag(tagTarget_outerSymbol_dict: Dict, taggedSymbols: Dict[str, str]):
        taggedTarget = []
        for tagTarget, outerSymbols in tagTarget_outerSymbol_dict.items():
            archs = set(["common"])

            for outerSymbol in outerSymbols:
                archs.add(taggedSymbols[outerSymbol])
            if "common" in archs and len(archs) > 1:
                archs.remove("common")
            taggedTarget.append((tagTarget[0], tagTarget[1], list(archs)))
        return taggedTarget
