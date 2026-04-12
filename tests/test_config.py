"""Tests for config file loading and merging."""

import json
import os

import pytest

from crap4py.config import load_config, merge_config_into_options
from crap4py.options import CliOptions


# ---------------------------------------------------------------------------
# load_config — explicit path
# ---------------------------------------------------------------------------


class TestLoadConfigExplicitPath:
    def test_explicit_path_found(self, tmp_path):
        cfg = tmp_path / "my.json"
        cfg.write_text(json.dumps({"src": "lib"}))
        result = load_config(explicit_path=str(cfg))
        assert result == {"src": "lib"}

    def test_explicit_path_not_found(self, tmp_path):
        missing = tmp_path / "nope.json"
        with pytest.raises(ValueError, match="Config file not found"):
            load_config(explicit_path=str(missing))

    def test_explicit_path_invalid_json(self, tmp_path):
        cfg = tmp_path / "bad.json"
        cfg.write_text("{not valid json!!")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_config(explicit_path=str(cfg))

    def test_explicit_path_non_dict(self, tmp_path):
        cfg = tmp_path / "list.json"
        cfg.write_text(json.dumps([1, 2, 3]))
        with pytest.raises(ValueError, match="must contain a JSON object"):
            load_config(explicit_path=str(cfg))

    def test_explicit_path_string_json(self, tmp_path):
        cfg = tmp_path / "str.json"
        cfg.write_text(json.dumps("hello"))
        with pytest.raises(ValueError, match="must contain a JSON object"):
            load_config(explicit_path=str(cfg))


# ---------------------------------------------------------------------------
# load_config — auto-discovery
# ---------------------------------------------------------------------------


class TestLoadConfigAutoDiscovery:
    def test_discovers_crap4py_config_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "crap4py.config.json").write_text(json.dumps({"src": "app"}))
        result = load_config()
        assert result == {"src": "app"}

    def test_discovers_crap4pyrc_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".crap4pyrc.json").write_text(json.dumps({"output": "json"}))
        result = load_config()
        assert result == {"output": "json"}

    def test_crap4py_config_json_takes_precedence(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "crap4py.config.json").write_text(json.dumps({"src": "first"}))
        (tmp_path / ".crap4pyrc.json").write_text(json.dumps({"src": "second"}))
        result = load_config()
        assert result == {"src": "first"}

    def test_no_config_found_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = load_config()
        assert result == {}

    def test_auto_discovery_invalid_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "crap4py.config.json").write_text("not json")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_config()

    def test_auto_discovery_non_dict(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "crap4py.config.json").write_text(json.dumps(42))
        with pytest.raises(ValueError, match="must contain a JSON object"):
            load_config()


# ---------------------------------------------------------------------------
# merge_config_into_options — field-by-field
# ---------------------------------------------------------------------------


class TestMergeConfigSrcDir:
    def test_config_overrides_default_src(self):
        opts = CliOptions()
        result = merge_config_into_options(opts, {"src": "lib"})
        assert result.src_dir == "lib"

    def test_cli_src_wins_over_config(self):
        opts = CliOptions(src_dir="custom")
        result = merge_config_into_options(opts, {"src": "lib"})
        assert result.src_dir == "custom"


class TestMergeConfigExcludes:
    def test_config_overrides_default_excludes(self):
        opts = CliOptions()
        result = merge_config_into_options(opts, {"exclude": ["vendor", "dist"]})
        assert result.excludes == ["vendor", "dist"]

    def test_cli_excludes_win_over_config(self):
        opts = CliOptions(excludes=["mine"])
        result = merge_config_into_options(opts, {"exclude": ["vendor"]})
        assert result.excludes == ["mine"]


class TestMergeConfigOutput:
    def test_config_overrides_default_output(self):
        opts = CliOptions()
        result = merge_config_into_options(opts, {"output": "json"})
        assert result.output == "json"

    def test_cli_output_wins_over_config(self):
        opts = CliOptions(output="csv")
        result = merge_config_into_options(opts, {"output": "json"})
        assert result.output == "csv"


class TestMergeConfigTimeout:
    def test_config_overrides_default_timeout(self):
        opts = CliOptions()
        result = merge_config_into_options(opts, {"timeout": 600})
        assert result.timeout_s == 600

    def test_cli_timeout_wins_over_config(self):
        opts = CliOptions(timeout_s=120)
        result = merge_config_into_options(opts, {"timeout": 600})
        assert result.timeout_s == 120


class TestMergeConfigRunner:
    def test_config_sets_runner(self):
        opts = CliOptions()
        result = merge_config_into_options(opts, {"runner": "pytest"})
        assert result.runner == "pytest"

    def test_cli_runner_wins(self):
        opts = CliOptions(runner="unittest")
        result = merge_config_into_options(opts, {"runner": "pytest"})
        assert result.runner == "unittest"


class TestMergeConfigCoverageCommand:
    def test_config_sets_coverage_command(self):
        opts = CliOptions()
        result = merge_config_into_options(opts, {"coverageCommand": "coverage run"})
        assert result.coverage_command == "coverage run"

    def test_cli_coverage_command_wins(self):
        opts = CliOptions(coverage_command="my-cmd")
        result = merge_config_into_options(opts, {"coverageCommand": "other"})
        assert result.coverage_command == "my-cmd"


class TestMergeConfigFailOnCrap:
    def test_config_sets_fail_on_crap(self):
        opts = CliOptions()
        result = merge_config_into_options(opts, {"failOnCrap": 30.0})
        assert result.fail_on_crap == 30.0

    def test_cli_fail_on_crap_wins(self):
        opts = CliOptions(fail_on_crap=10.0)
        result = merge_config_into_options(opts, {"failOnCrap": 30.0})
        assert result.fail_on_crap == 10.0


class TestMergeConfigFailOnComplexity:
    def test_config_sets_fail_on_complexity(self):
        opts = CliOptions()
        result = merge_config_into_options(opts, {"failOnComplexity": 20.0})
        assert result.fail_on_complexity == 20.0

    def test_cli_fail_on_complexity_wins(self):
        opts = CliOptions(fail_on_complexity=5.0)
        result = merge_config_into_options(opts, {"failOnComplexity": 20.0})
        assert result.fail_on_complexity == 5.0


class TestMergeConfigFailOnCoverageBelow:
    def test_config_sets_fail_on_coverage_below(self):
        opts = CliOptions()
        result = merge_config_into_options(opts, {"failOnCoverageBelow": 80.0})
        assert result.fail_on_coverage_below == 80.0

    def test_cli_fail_on_coverage_below_wins(self):
        opts = CliOptions(fail_on_coverage_below=90.0)
        result = merge_config_into_options(opts, {"failOnCoverageBelow": 80.0})
        assert result.fail_on_coverage_below == 90.0


class TestMergeConfigTop:
    def test_config_sets_top(self):
        opts = CliOptions()
        result = merge_config_into_options(opts, {"top": 10})
        assert result.top == 10

    def test_cli_top_wins(self):
        opts = CliOptions(top=5)
        result = merge_config_into_options(opts, {"top": 10})
        assert result.top == 5


class TestMergeConfigReturnsNewInstance:
    def test_returns_new_instance(self):
        opts = CliOptions()
        result = merge_config_into_options(opts, {"src": "lib"})
        assert result is not opts

    def test_original_unchanged(self):
        opts = CliOptions()
        merge_config_into_options(opts, {"src": "lib"})
        assert opts.src_dir == "src"


class TestMergeConfigEmptyConfig:
    def test_empty_config_preserves_defaults(self):
        opts = CliOptions()
        result = merge_config_into_options(opts, {})
        assert result.src_dir == "src"
        assert result.output == "text"
        assert result.timeout_s == 300
        assert result.excludes == []
        assert result.runner is None
        assert result.coverage_command is None
        assert result.fail_on_crap is None
        assert result.fail_on_complexity is None
        assert result.fail_on_coverage_below is None
        assert result.top is None


class TestMergeConfigMultipleFields:
    def test_multiple_config_fields(self):
        opts = CliOptions()
        config = {
            "src": "lib",
            "output": "json",
            "timeout": 600,
            "runner": "pytest",
            "coverageCommand": "coverage run",
            "failOnCrap": 30.0,
            "exclude": ["vendor"],
            "top": 20,
        }
        result = merge_config_into_options(opts, config)
        assert result.src_dir == "lib"
        assert result.output == "json"
        assert result.timeout_s == 600
        assert result.runner == "pytest"
        assert result.coverage_command == "coverage run"
        assert result.fail_on_crap == 30.0
        assert result.excludes == ["vendor"]
        assert result.top == 20

    def test_cli_overrides_mixed(self):
        opts = CliOptions(src_dir="my_src", runner="unittest")
        config = {
            "src": "lib",
            "runner": "pytest",
            "output": "json",
            "failOnCrap": 30.0,
        }
        result = merge_config_into_options(opts, config)
        assert result.src_dir == "my_src"  # CLI wins
        assert result.runner == "unittest"  # CLI wins
        assert result.output == "json"  # config applies (CLI was default)
        assert result.fail_on_crap == 30.0  # config applies (CLI was None)


class TestMergePreservesNonConfigFields:
    def test_mode_and_filters_preserved(self):
        opts = CliOptions(mode="report", filters=["test_foo"])
        result = merge_config_into_options(opts, {"src": "lib"})
        assert result.mode == "report"
        assert result.filters == ["test_foo"]

    def test_config_path_preserved(self):
        opts = CliOptions(config_path="my.json")
        result = merge_config_into_options(opts, {})
        assert result.config_path == "my.json"
