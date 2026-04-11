import os
import subprocess
import sys

from crap4py.core import analyze_file, filter_sources, find_source_files
from crap4py.coverage_parser import parse_coverage
from crap4py.crap import format_report, sort_by_crap

DEFAULT_TIMEOUT = 300


def main():
    # Route skill subcommand before the normal CRAP flow
    if len(sys.argv) > 1 and sys.argv[1] == "skill":
        from crap4py.skill_cmd import run_skill_cmd
        run_skill_cmd(sys.argv[2:])
        return

    for f in (".coverage", "coverage.json"):
        if os.path.exists(f):
            try:
                os.remove(f)
            except OSError:
                pass

    try:
        result = subprocess.run([sys.executable, "-m", "coverage", "run", "-m", "pytest"], timeout=DEFAULT_TIMEOUT)
    except subprocess.TimeoutExpired:
        print(f"coverage run timed out after {DEFAULT_TIMEOUT}s")
        sys.exit(1)
    if result.returncode != 0:
        print(f"Coverage failed (exit {result.returncode})")
        sys.exit(1)

    try:
        result = subprocess.run([sys.executable, "-m", "coverage", "json"], timeout=DEFAULT_TIMEOUT)
    except subprocess.TimeoutExpired:
        print(f"coverage json timed out after {DEFAULT_TIMEOUT}s")
        sys.exit(1)
    if result.returncode != 0:
        print(f"coverage json failed (exit {result.returncode})")
        sys.exit(1)

    module_filters = sys.argv[1:]
    sources = find_source_files()
    filtered = filter_sources(sources, module_filters)

    files_data = parse_coverage("coverage.json")
    all_entries = []
    for source_path in filtered:
        all_entries.extend(analyze_file(source_path, files_data))

    sorted_entries = sort_by_crap(all_entries)
    print(format_report(sorted_entries))


if __name__ == "__main__":
    main()
