"""crap4py — CRAP metric for Python projects."""
from crap4py.api import generate_report
from crap4py.complexity import extract_functions
from crap4py.core import filter_sources, find_source_files
from crap4py.coverage_parser import coverage_for_range, normalize_path, parse_coverage, source_to_module
from crap4py.crap import (
    crap_score,
    format_csv_report,
    format_json_report,
    format_markdown_report,
    format_report,
    sort_by_crap,
)
from crap4py.models import CrapEntry, FunctionInfo

__all__ = [
    "generate_report",
    "extract_functions",
    "find_source_files",
    "filter_sources",
    "parse_coverage",
    "coverage_for_range",
    "source_to_module",
    "normalize_path",
    "crap_score",
    "sort_by_crap",
    "format_report",
    "format_json_report",
    "format_markdown_report",
    "format_csv_report",
    "CrapEntry",
    "FunctionInfo",
]
