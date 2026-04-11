from dataclasses import dataclass


@dataclass
class FunctionInfo:
    name: str
    start_line: int
    end_line: int
    complexity: int


@dataclass
class CrapEntry:
    name: str
    module: str
    complexity: int
    coverage: float
    crap: float
