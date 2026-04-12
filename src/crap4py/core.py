import glob as _glob
import warnings

from crap4py.complexity import extract_functions
from crap4py.coverage_parser import coverage_for_range, source_to_module
from crap4py.crap import crap_score
from crap4py.models import CrapEntry


def find_source_files_with_options(src_dirs, excludes):
    """Find .py files across multiple src dirs, filtering by exclude patterns."""
    file_set = set()
    for src_dir in src_dirs:
        for f in _glob.glob(f"{src_dir}/**/*.py", recursive=True):
            if not any(ex in f for ex in excludes):
                file_set.add(f)
    return sorted(file_set)


def find_source_files(source_dir="src"):
    """Find all .py files under source_dir/, sorted."""
    return find_source_files_with_options(src_dirs=[source_dir], excludes=[])


def filter_sources(files, module_filters):
    """Return files matching any of the module_filters substrings (or all if empty)."""
    if not module_filters:
        return files
    return [f for f in files if any(filt in f for filt in module_filters)]


def build_entries(fns, file_data, module):
    """Build CRAP report entries for a list of extracted functions."""
    entries = []
    for f in fns:
        cov = coverage_for_range(file_data, f.start_line, f.end_line)
        score = crap_score(f.complexity, cov)
        entries.append(CrapEntry(
            name=f.name,
            module=module,
            complexity=f.complexity,
            coverage=cov,
            crap=score,
        ))
    return entries


def analyze_file(source_path, files_data, source_dir="src"):
    """Analyze a single source file: extract functions, look up coverage, build entries."""
    with open(source_path) as fh:
        source = fh.read()
    try:
        fns = extract_functions(source)
    except SyntaxError as e:
        warnings.warn(f"Skipping {source_path}: {e}")
        return []
    module = source_to_module(source_path, source_dir=source_dir)
    file_data = files_data.get(source_path, {"executed_lines": [], "missing_lines": []})
    return build_entries(fns, file_data, module)
