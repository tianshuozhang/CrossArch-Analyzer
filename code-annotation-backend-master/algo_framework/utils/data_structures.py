from typing import Generic, NamedTuple, TypeVar, Optional
from dataclasses import dataclass, field

T = TypeVar("T")


# projectIterator


@dataclass(frozen=True)
class FileResultDict(Generic[T]):
    data: dict[str, T]

    def __getitem__(self, key: str) -> T:
        return self.data[key]

    def __contains__(self, key: str) -> bool:
        return key in self.data


# CodeRewritter

VectorType = int


class ModifyPattern(NamedTuple):
    before_pattern: str
    after_pattern: str


# CodeAnalyzer


class TagTargetInfo(NamedTuple):
    start_line: int
    end_line: int


@dataclass
class CodeNode:
    name: str
    syntax: str = "other"
    archs: set[str] = field(default_factory=set)
    info: Optional[TagTargetInfo] = None


class DepRelation(NamedTuple):
    node: CodeNode
    dependencies: list[CodeNode]


# static_classify_tool
class TreeSitterAnalysisResult(NamedTuple):
    tagTarget_relations: list[DepRelation]
    symbol_relations: list[DepRelation]


class ErrorSnippet(NamedTuple):
    start_line: int
    end_line: int
    code_content: str


class TreeSitterOutput(NamedTuple):
    tree_sitter_analysis_result: TreeSitterAnalysisResult
    error_snippets: list[ErrorSnippet]
