import json
import pytest
from crap4py.coverage_parser import CoverageSchemaError, coverage_for_range, parse_coverage, source_to_module


class TestCoverageForRange:
    def test_full_coverage(self):
        file_data = {"executed_lines": [1, 2, 3], "missing_lines": []}
        assert coverage_for_range(file_data, 1, 3) == 100.0

    def test_no_coverage(self):
        file_data = {"executed_lines": [], "missing_lines": [1, 2, 3]}
        assert coverage_for_range(file_data, 1, 3) == 0.0

    def test_partial_coverage(self):
        file_data = {"executed_lines": [1, 2], "missing_lines": [3]}
        result = coverage_for_range(file_data, 1, 3)
        assert abs(result - 66.67) < 0.1

    def test_no_instrumented_lines(self):
        file_data = {"executed_lines": [], "missing_lines": []}
        assert coverage_for_range(file_data, 1, 5) == 100.0

    def test_only_lines_in_range_counted(self):
        file_data = {"executed_lines": [1, 2, 10, 11], "missing_lines": [3]}
        # Range 1-3: executed=[1,2], missing=[3] -> 2/3
        result = coverage_for_range(file_data, 1, 3)
        assert abs(result - 66.67) < 0.1

    def test_multi_line_function(self):
        file_data = {
            "executed_lines": [3, 4],
            "missing_lines": [5],
        }
        result = coverage_for_range(file_data, 3, 5)
        assert abs(result - 66.67) < 0.1


class TestSourceToModule:
    def test_simple_path(self):
        assert source_to_module("src/foo/bar.py") == "foo.bar"

    def test_nested_path(self):
        assert source_to_module("src/crap4py/complexity.py") == "crap4py.complexity"

    def test_single_module(self):
        assert source_to_module("src/mymodule.py") == "mymodule"

    def test_custom_source_dir(self):
        assert source_to_module("lib/foo/bar.py", source_dir="lib") == "foo.bar"

    def test_custom_source_dir_nested(self):
        assert source_to_module("packages/myapp/core.py", source_dir="packages") == "myapp.core"

    def test_custom_source_dir_no_match(self):
        assert source_to_module("other/foo/bar.py", source_dir="lib") == "other.foo.bar"


class TestParseCoverage:
    def test_parses_files_dict(self, tmp_path):
        data = {
            "files": {
                "src/foo/bar.py": {
                    "executed_lines": [1, 2],
                    "missing_lines": [3],
                }
            }
        }
        json_file = tmp_path / "coverage.json"
        json_file.write_text(json.dumps(data))
        result = parse_coverage(str(json_file))
        assert "src/foo/bar.py" in result
        assert result["src/foo/bar.py"]["executed_lines"] == [1, 2]
        assert result["src/foo/bar.py"]["missing_lines"] == [3]

    def test_empty_files(self, tmp_path):
        data = {"files": {}}
        json_file = tmp_path / "coverage.json"
        json_file.write_text(json.dumps(data))
        assert parse_coverage(str(json_file)) == {}

    def test_parse_coverage_file_not_found(self, tmp_path):
        with pytest.raises(CoverageSchemaError, match="Coverage file not found"):
            parse_coverage(str(tmp_path / "nonexistent.json"))

    def test_parse_coverage_invalid_json(self, tmp_path):
        json_file = tmp_path / "coverage.json"
        json_file.write_text("{not valid json")
        with pytest.raises(CoverageSchemaError, match="Invalid JSON"):
            parse_coverage(str(json_file))

    def test_parse_coverage_missing_files_key(self, tmp_path):
        json_file = tmp_path / "coverage.json"
        json_file.write_text(json.dumps({"meta": {}}))
        with pytest.raises(CoverageSchemaError, match="Missing 'files' key"):
            parse_coverage(str(json_file))

    def test_parse_coverage_files_not_dict(self, tmp_path):
        json_file = tmp_path / "coverage.json"
        json_file.write_text(json.dumps({"files": [1, 2, 3]}))
        with pytest.raises(CoverageSchemaError, match="'files' must be a dict"):
            parse_coverage(str(json_file))

    def test_parse_coverage_top_level_not_dict(self, tmp_path):
        json_file = tmp_path / "coverage.json"
        json_file.write_text(json.dumps([1, 2, 3]))
        with pytest.raises(CoverageSchemaError, match="Expected top-level dict"):
            parse_coverage(str(json_file))

    def test_parse_coverage_entry_not_dict(self, tmp_path):
        json_file = tmp_path / "coverage.json"
        json_file.write_text(json.dumps({"files": {"src/foo.py": "not-a-dict"}}))
        with pytest.raises(CoverageSchemaError, match="Entry for 'src/foo.py' must be a dict"):
            parse_coverage(str(json_file))
