import os
import subprocess
import sys

from crap4py.core import analyze_file, filter_sources, find_source_files
from crap4py.coverage_parser import parse_coverage
from crap4py.crap import format_report, sort_by_crap

DEFAULT_TIMEOUT = 300


def _handle_skill_command():
    if len(sys.argv) > 1 and sys.argv[1] == "skill":
        from crap4py.skill_cmd import run_skill_cmd
        run_skill_cmd(sys.argv[2:])
        return True
    return False


def _remove_stale_coverage_files():
    for f in (".coverage", "coverage.json"):
        if os.path.exists(f):
            try:
                os.remove(f)
            except OSError:
                pass


def _run_subprocess_step(cmd, label):
    try:
        result = subprocess.run(cmd, timeout=DEFAULT_TIMEOUT)
    except subprocess.TimeoutExpired:
        print(f"{label} timed out after {DEFAULT_TIMEOUT}s")
        sys.exit(1)
    if result.returncode != 0:
        print(f"{label} failed (exit {result.returncode})")
        sys.exit(1)


def _run_coverage():
    _run_subprocess_step(
        [sys.executable, "-m", "coverage", "run", "-m", "pytest"],
        "coverage run",
    )
    _run_subprocess_step(
        [sys.executable, "-m", "coverage", "json"],
        "coverage json",
    )


def _build_report(module_filters):
    sources = find_source_files()
    filtered = filter_sources(sources, module_filters)
    files_data = parse_coverage("coverage.json")
    all_entries = []
    for source_path in filtered:
        all_entries.extend(analyze_file(source_path, files_data))
    return format_report(sort_by_crap(all_entries))


def main():
    if _handle_skill_command():
        return
    _remove_stale_coverage_files()
    _run_coverage()
    print(_build_report(sys.argv[1:]))


if __name__ == "__main__":
    main()
