import json


class CoverageSchemaError(ValueError):
    """Raised when the coverage JSON file is missing, malformed, or has an unexpected schema."""


def _load_coverage_json(json_path):
    try:
        with open(json_path) as f:
            return json.load(f)
    except FileNotFoundError:
        raise CoverageSchemaError(f"Coverage file not found: {json_path}")
    except json.JSONDecodeError as exc:
        raise CoverageSchemaError(f"Invalid JSON in {json_path}: {exc}") from exc


def _validate_coverage_schema(data, json_path):
    if not isinstance(data, dict):
        raise CoverageSchemaError(f"Expected top-level dict in {json_path}")
    if "files" not in data:
        raise CoverageSchemaError(f"Missing 'files' key in {json_path}")
    files = data["files"]
    if not isinstance(files, dict):
        raise CoverageSchemaError(f"'files' must be a dict in {json_path}")
    for path, entry in files.items():
        if not isinstance(entry, dict):
            raise CoverageSchemaError(f"Entry for '{path}' must be a dict in {json_path}")
    return files


def parse_coverage(json_path="coverage.json"):
    """Parse coverage.py JSON output. Returns dict of file_path -> file_data."""
    data = _load_coverage_json(json_path)
    return _validate_coverage_schema(data, json_path)


def coverage_for_range(file_data, start_line, end_line):
    """Compute coverage percentage for lines in [start_line, end_line]."""
    executed = set(file_data.get("executed_lines", []))
    missing = set(file_data.get("missing_lines", []))
    lines = set(range(start_line, end_line + 1))
    covered = len(executed & lines)
    uncovered = len(missing & lines)
    total = covered + uncovered
    if total == 0:
        return 100.0
    return 100.0 * covered / total


def source_to_module(source_path, source_dir="src"):
    """Convert a source path to a dotted module name.

    Example: 'src/foo/bar.py' -> 'foo.bar'
    """
    path = source_path
    prefix_fwd = source_dir + "/"
    prefix_bwd = source_dir + "\\"
    if path.startswith(prefix_fwd) or path.startswith(prefix_bwd):
        path = path[len(prefix_fwd):]
    if path.endswith(".py"):
        path = path[:-3]
    return path.replace("\\", ".").replace("/", ".")
