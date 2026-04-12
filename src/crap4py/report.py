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
    checks = [
        (opts.fail_on_crap, lambda e: e.crap >= opts.fail_on_crap, "exceed", "CRAP"),
        (opts.fail_on_complexity, lambda e: e.complexity >= opts.fail_on_complexity, "exceed", "complexity"),
        (opts.fail_on_coverage_below, lambda e: e.coverage < opts.fail_on_coverage_below, "below", "coverage"),
    ]
    for threshold, predicate, verb, label in checks:
        if threshold is not None:
            violators = [e for e in entries if predicate(e)]
            if violators:
                return (
                    f"CI failed: {len(violators)} function(s) {verb} "
                    f"{label} threshold of {threshold}"
                )

    return None


def _run_subprocess(cmd, *, shell=False, timeout=None, label="command"):
    """Run a subprocess, returning True on success."""
    try:
        result = subprocess.run(
            cmd, shell=shell, timeout=timeout,
            capture_output=True, text=True,
        )
    except subprocess.TimeoutExpired:
        print(f"{label} timed out", file=sys.stderr)
        return False
    if result.returncode != 0:
        print(f"{label} failed", file=sys.stderr)
        return False
    return True


def _build_coverage_command(opts):
    """Build the coverage run command. Returns (cmd, shell)."""
    if opts.coverage_command:
        return opts.coverage_command, True
    runner = opts.runner or detect_runner()
    if runner == "unittest":
        return [
            sys.executable, "-m", "coverage", "run",
            "-m", "unittest", "discover",
        ], False
    return [sys.executable, "-m", "coverage", "run", "-m", "pytest"], False


def _run_coverage_step(opts):
    """Run the coverage collection step. Returns True on success, False on failure."""
    for stale in (".coverage", "coverage.json"):
        if os.path.exists(stale):
            os.remove(stale)

    cmd_run, use_shell = _build_coverage_command(opts)

    if not _run_subprocess(
        cmd_run, shell=use_shell, timeout=opts.timeout_s, label="coverage run",
    ):
        return False

    return _run_subprocess(
        [sys.executable, "-m", "coverage", "json"],
        timeout=opts.timeout_s, label="coverage json",
    )


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
