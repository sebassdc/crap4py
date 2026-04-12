import os
import pytest
from crap4py.core import analyze_file, find_source_files_with_options, filter_sources
from crap4py.coverage_parser import parse_coverage
from crap4py.crap import sort_by_crap
from crap4py.options import parse_options

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestBasicProjectFixture:
    def test_analyze_fixture_project(self):
        project = os.path.join(FIXTURES, "basic-project")
        src_dir = os.path.join(project, "src")
        cov_path = os.path.join(project, "coverage.json")
        files = find_source_files_with_options(src_dirs=[src_dir], excludes=[])
        files_data = parse_coverage(cov_path)
        entries = []
        for f in files:
            entries.extend(analyze_file(f, files_data, source_dir=src_dir))
        assert len(entries) == 2
        names = {e.name for e in entries}
        assert "add" in names
        assert "multiply" in names

    def test_entries_have_valid_scores(self):
        project = os.path.join(FIXTURES, "basic-project")
        src_dir = os.path.join(project, "src")
        cov_path = os.path.join(project, "coverage.json")
        files = find_source_files_with_options(src_dirs=[src_dir], excludes=[])
        files_data = parse_coverage(cov_path)
        entries = []
        for f in files:
            entries.extend(analyze_file(f, files_data, source_dir=src_dir))
        for e in entries:
            assert e.crap > 0
            assert e.complexity >= 1
            assert 0 <= e.coverage <= 100

    def test_filter_narrows_results(self):
        project = os.path.join(FIXTURES, "basic-project")
        src_dir = os.path.join(project, "src")
        files = find_source_files_with_options(src_dirs=[src_dir], excludes=[])
        filtered = filter_sources(files, ["nonexistent"])
        assert len(filtered) == 0

    def test_sort_by_crap_orders_correctly(self):
        project = os.path.join(FIXTURES, "basic-project")
        src_dir = os.path.join(project, "src")
        cov_path = os.path.join(project, "coverage.json")
        files = find_source_files_with_options(src_dirs=[src_dir], excludes=[])
        files_data = parse_coverage(cov_path)
        entries = []
        for f in files:
            entries.extend(analyze_file(f, files_data, source_dir=src_dir))
        sorted_entries = sort_by_crap(entries)
        for i in range(len(sorted_entries) - 1):
            assert sorted_entries[i].crap >= sorted_entries[i+1].crap


class TestMissingCoverageFixture:
    def test_missing_coverage_raises(self):
        project = os.path.join(FIXTURES, "missing-coverage")
        cov_path = os.path.join(project, "coverage.json")
        from crap4py.coverage_parser import CoverageSchemaError
        with pytest.raises(CoverageSchemaError, match="not found"):
            parse_coverage(cov_path)


class TestCliOptionsCombinations:
    def test_all_flags_together(self):
        opts = parse_options([
            "--src", "lib",
            "--exclude", "dist",
            "--exclude", "test",
            "--output", "markdown",
            "--runner", "pytest",
            "--fail-on-crap", "30",
            "--fail-on-complexity", "15",
            "--fail-on-coverage-below", "70",
            "--top", "10",
            "--timeout", "120",
            "--config", "my.json",
            "parser",
            "validator",
        ])
        assert opts.src_dir == "lib"
        assert opts.excludes == ["dist", "test"]
        assert opts.output == "markdown"
        assert opts.runner == "pytest"
        assert opts.fail_on_crap == 30.0
        assert opts.fail_on_complexity == 15.0
        assert opts.fail_on_coverage_below == 70.0
        assert opts.top == 10
        assert opts.timeout_s == 120
        assert opts.config_path == "my.json"
        assert opts.filters == ["parser", "validator"]

    def test_json_shorthand(self):
        opts = parse_options(["--json"])
        assert opts.output == "json"

    def test_help_overrides_everything(self):
        opts = parse_options(["--help", "--src", "lib", "--json"])
        assert opts.mode == "help"
