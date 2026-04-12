"""Programmatic API for crap4py. Does NOT run test suites — reads existing coverage data."""
import os
from crap4py.core import analyze_file, filter_sources, find_source_files_with_options
from crap4py.coverage_parser import parse_coverage
from crap4py.crap import sort_by_crap


def generate_report(src_dir="src", coverage_path="coverage.json", filters=None, excludes=None):
    """Analyze source files against existing coverage data.
    Returns dict with 'entries' key containing list of result dicts.
    """
    if not os.path.exists(coverage_path):
        raise FileNotFoundError(f"Coverage file not found: {coverage_path}")

    files = find_source_files_with_options(
        src_dirs=[src_dir],
        excludes=excludes or [],
    )
    filtered = filter_sources(files, filters or [])
    files_data = parse_coverage(coverage_path)

    entries = []
    for f in filtered:
        entries.extend(analyze_file(f, files_data, source_dir=src_dir))

    sorted_entries = sort_by_crap(entries)
    return {
        "entries": [
            {
                "name": e.name,
                "module": e.module,
                "complexity": e.complexity,
                "coverage": e.coverage,
                "crap": round(e.crap, 1),
            }
            for e in sorted_entries
        ]
    }
