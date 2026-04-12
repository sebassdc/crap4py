"""Tests for crap4py.api — programmatic API."""

import json
from unittest.mock import patch

import pytest

from crap4py.api import generate_report
from crap4py.models import CrapEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_coverage_json(path, files_data=None):
    """Write a minimal coverage.json file."""
    data = {"files": files_data or {}}
    path.write_text(json.dumps(data))


def _write_source(directory, filename, content):
    """Write a Python source file under a directory."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(content)


# ---------------------------------------------------------------------------
# TestGenerateReport
# ---------------------------------------------------------------------------

class TestGenerateReport:
    def test_analyzes_own_source(self, tmp_path, monkeypatch):
        """generate_report reads existing coverage data and returns entries."""
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "src" / "pkg"
        src.mkdir(parents=True)
        (src / "mod.py").write_text(
            "def foo(x):\n    if x:\n        return 1\n    return 0\n"
        )
        cov_path = tmp_path / "coverage.json"
        _write_coverage_json(cov_path, {
            str(src / "mod.py"): {
                "executed_lines": [1, 2, 3],
                "missing_lines": [4],
            }
        })

        result = generate_report(
            src_dir="src",
            coverage_path=str(cov_path),
        )

        assert "entries" in result
        assert len(result["entries"]) == 1
        entry = result["entries"][0]
        assert entry["name"] == "foo"
        assert entry["module"] == "pkg.mod"
        assert entry["complexity"] == 2
        assert isinstance(entry["coverage"], float)
        assert isinstance(entry["crap"], float)

    def test_with_filters(self, tmp_path, monkeypatch):
        """Filters limit which source files are analyzed."""
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "src" / "pkg"
        src.mkdir(parents=True)
        (src / "complexity.py").write_text("def analyze():\n    return 1\n")
        (src / "other.py").write_text("def helper():\n    return 2\n")
        cov_path = tmp_path / "coverage.json"
        _write_coverage_json(cov_path)

        result = generate_report(
            src_dir="src",
            coverage_path=str(cov_path),
            filters=["complexity"],
        )

        assert "entries" in result
        names = [e["name"] for e in result["entries"]]
        assert "analyze" in names
        assert "helper" not in names

    def test_with_excludes(self, tmp_path, monkeypatch):
        """Excludes remove matching source files from analysis."""
        monkeypatch.chdir(tmp_path)
        src = tmp_path / "src" / "pkg"
        src.mkdir(parents=True)
        (src / "keep.py").write_text("def kept():\n    return 1\n")
        (src / "skill_cmd.py").write_text("def skipped():\n    return 2\n")
        cov_path = tmp_path / "coverage.json"
        _write_coverage_json(cov_path)

        result = generate_report(
            src_dir="src",
            coverage_path=str(cov_path),
            excludes=["skill"],
        )

        names = [e["name"] for e in result["entries"]]
        assert "kept" in names
        assert "skipped" not in names

    def test_missing_coverage_raises(self):
        """FileNotFoundError is raised when coverage file does not exist."""
        with pytest.raises(FileNotFoundError, match="Coverage file not found"):
            generate_report(coverage_path="/nonexistent/coverage.json")


# ---------------------------------------------------------------------------
# TestPublicImports
# ---------------------------------------------------------------------------

class TestPublicImports:
    def test_all_exports_importable(self):
        """All public symbols are importable from crap4py."""
        from crap4py import (
            generate_report,
            crap_score,
            extract_functions,
            parse_coverage,
            sort_by_crap,
            format_report,
            format_json_report,
            format_markdown_report,
            format_csv_report,
            CrapEntry,
            FunctionInfo,
            find_source_files,
            filter_sources,
            coverage_for_range,
            source_to_module,
            normalize_path,
        )
        # Verify they are callable or classes
        assert callable(generate_report)
        assert callable(crap_score)
        assert callable(extract_functions)
        assert callable(parse_coverage)
        assert callable(sort_by_crap)
        assert callable(format_report)
        assert callable(format_json_report)
        assert callable(format_markdown_report)
        assert callable(format_csv_report)
        assert callable(find_source_files)
        assert callable(filter_sources)
        assert callable(coverage_for_range)
        assert callable(source_to_module)
        assert callable(normalize_path)
        assert CrapEntry is not None
        assert FunctionInfo is not None
