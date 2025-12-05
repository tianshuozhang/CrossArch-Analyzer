from typing import Dict, List, Tuple


class TargetTagger:
    def tag(tagTarget_outerSymbol_dict: Dict, taggedSymbols: Dict[str, str]):
        taggedTarget = []
        for tagTarget, outerSymbols in enumerate(tagTarget_outerSymbol_dict):
            archs = set()
            for outerSymbol in outerSymbols:
                archs.add(taggedSymbols[outerSymbol])
            taggedTarget.append((tagTarget[0], tagTarget[1], list(archs)))
        return taggedTarget
