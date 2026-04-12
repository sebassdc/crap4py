"""Report orchestration — run coverage, analyze files, format and check thresholds."""

import os
import subprocess
import sys

from crap4py.core import find_source_files_with_options, filter_sources, analyze_file
from crap4py.coverage_parser import parse_coverage
from crap4py.crap import (
    format_report,
    format_json_report,
    format_markdown_report,
    format_csv_report,
    sort_by_crap,
)


def detect_runner():
    """Detect the test runner. Defaults to pytest for Python projects."""
    return "pytest"


def evaluate_thresholds(entries, opts):
    """Check entries against threshold options.

    Returns a failure message string if any threshold is exceeded, or None.
    """
    if opts.fail_on_crap is not None:
        violators = [e for e in entries if e.crap >= opts.fail_on_crap]
        if violators:
            return (
                f"CI failed: {len(violators)} function(s) exceed "
                f"CRAP threshold of {opts.fail_on_crap}"
            )

    if opts.fail_on_complexity is not None:
        violators = [e for e in entries if e.complexity >= opts.fail_on_complexity]
        if violators:
            return (
                f"CI failed: {len(violators)} function(s) exceed "
                f"complexity threshold of {opts.fail_on_complexity}"
            )

    if opts.fail_on_coverage_below is not None:
        violators = [e for e in entries if e.coverage < opts.fail_on_coverage_below]
        if violators:
            return (
                f"CI failed: {len(violators)} function(s) below "
                f"coverage threshold of {opts.fail_on_coverage_below}"
            )

    return None


def _run_coverage_step(opts):
    """Run the coverage collection step. Returns True on success, False on failure."""
    # Clean stale files
    for stale in (".coverage", "coverage.json"):
        if os.path.exists(stale):
            os.remove(stale)

    timeout = opts.timeout_s

    # Step 1: run tests with coverage
    if opts.coverage_command:
        cmd_run = opts.coverage_command
        use_shell = True
    else:
        runner = opts.runner or detect_runner()
        if runner == "unittest":
            cmd_run = [
                sys.executable, "-m", "coverage", "run",
                "-m", "unittest", "discover",
            ]
        else:
            cmd_run = [
                sys.executable, "-m", "coverage", "run", "-m", "pytest",
            ]
        use_shell = False

    try:
        result = subprocess.run(
            cmd_run, shell=use_shell, timeout=timeout,
            capture_output=True, text=True,
        )
    except subprocess.TimeoutExpired:
        print("coverage run timed out", file=sys.stderr)
        return False

    if result.returncode != 0:
        print("coverage run failed", file=sys.stderr)
        return False

    # Step 2: generate JSON report
    cmd_json = [sys.executable, "-m", "coverage", "json"]
    try:
        result = subprocess.run(
            cmd_json, timeout=timeout, capture_output=True, text=True,
        )
    except subprocess.TimeoutExpired:
        print("coverage json timed out", file=sys.stderr)
        return False

    if result.returncode != 0:
        print("coverage json failed", file=sys.stderr)
        return False

    return True


def run_report(opts):
    """Run the full CRAP report pipeline. Returns exit code (0 or 1)."""
    # Validate src_dir
    if not os.path.isdir(opts.src_dir):
        print(f"Source directory does not exist: {opts.src_dir}", file=sys.stderr)
        return 1

    # Find files
    all_files = find_source_files_with_options(
        src_dirs=[opts.src_dir], excludes=opts.excludes,
    )
    if not all_files:
        print("No Python files found", file=sys.stderr)
        return 1

    # Filter
    matched_files = filter_sources(all_files, opts.filters)
    if not matched_files:
        print("No files match the filters", file=sys.stderr)
        return 1

    # Run coverage
    if not _run_coverage_step(opts):
        return 1

    # Parse coverage
    files_data = parse_coverage()

    # Analyze all files
    all_entries = []
    for f in matched_files:
        all_entries.extend(analyze_file(f, files_data, source_dir=opts.src_dir))

    # Sort
    sorted_entries = sort_by_crap(all_entries)

    # Apply --top limit for display
    display_entries = sorted_entries
    if opts.top is not None:
        display_entries = sorted_entries[: opts.top]

    # Format output
    formatters = {
        "text": format_report,
        "json": format_json_report,
        "markdown": format_markdown_report,
        "csv": format_csv_report,
    }
    formatter = formatters.get(opts.output, format_report)
    print(formatter(display_entries))

    # Evaluate thresholds on ALL entries (not just displayed)
    failure_msg = evaluate_thresholds(sorted_entries, opts)
    if failure_msg:
        print(failure_msg, file=sys.stderr)
        return 1

    return 0
