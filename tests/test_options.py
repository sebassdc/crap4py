"""Tests for CLI options parsing."""

import math
import pytest
from crap4py.options import CliOptions, parse_options


class TestCliOptionsDefaults:
    def test_default_mode(self):
        opts = parse_options([])
        assert opts.mode == "report"

    def test_default_filters(self):
        opts = parse_options([])
        assert opts.filters == []

    def test_default_src_dir(self):
        opts = parse_options([])
        assert opts.src_dir == "src"

    def test_default_timeout(self):
        opts = parse_options([])
        assert opts.timeout_s == 300

    def test_default_output(self):
        opts = parse_options([])
        assert opts.output == "text"

    def test_default_excludes(self):
        opts = parse_options([])
        assert opts.excludes == []

    def test_default_runner(self):
        opts = parse_options([])
        assert opts.runner is None

    def test_default_coverage_command(self):
        opts = parse_options([])
        assert opts.coverage_command is None

    def test_default_fail_on_crap(self):
        opts = parse_options([])
        assert opts.fail_on_crap is None

    def test_default_fail_on_complexity(self):
        opts = parse_options([])
        assert opts.fail_on_complexity is None

    def test_default_fail_on_coverage_below(self):
        opts = parse_options([])
        assert opts.fail_on_coverage_below is None

    def test_default_top(self):
        opts = parse_options([])
        assert opts.top is None

    def test_default_config_path(self):
        opts = parse_options([])
        assert opts.config_path is None


class TestHelpFlag:
    def test_help_long(self):
        opts = parse_options(["--help"])
        assert opts.mode == "help"

    def test_help_short(self):
        opts = parse_options(["-h"])
        assert opts.mode == "help"


class TestVersionFlag:
    def test_version_long(self):
        opts = parse_options(["--version"])
        assert opts.mode == "version"

    def test_version_short(self):
        opts = parse_options(["-v"])
        assert opts.mode == "version"


class TestJsonFlag:
    def test_json_shorthand(self):
        opts = parse_options(["--json"])
        assert opts.output == "json"


class TestOutputFlag:
    def test_output_text(self):
        opts = parse_options(["--output", "text"])
        assert opts.output == "text"

    def test_output_json(self):
        opts = parse_options(["--output", "json"])
        assert opts.output == "json"

    def test_output_markdown(self):
        opts = parse_options(["--output", "markdown"])
        assert opts.output == "markdown"

    def test_output_csv(self):
        opts = parse_options(["--output", "csv"])
        assert opts.output == "csv"

    def test_output_invalid(self):
        with pytest.raises(ValueError, match="Invalid output format"):
            parse_options(["--output", "xml"])

    def test_output_missing_value(self):
        with pytest.raises(ValueError, match="--output requires a value"):
            parse_options(["--output"])


class TestSrcFlag:
    def test_src_dir(self):
        opts = parse_options(["--src", "lib"])
        assert opts.src_dir == "lib"

    def test_src_missing_value(self):
        with pytest.raises(ValueError, match="--src requires a value"):
            parse_options(["--src"])


class TestTimeoutFlag:
    def test_timeout(self):
        opts = parse_options(["--timeout", "60"])
        assert opts.timeout_s == 60

    def test_timeout_missing_value(self):
        with pytest.raises(ValueError, match="--timeout requires a value"):
            parse_options(["--timeout"])

    def test_timeout_not_a_number(self):
        with pytest.raises(ValueError, match="--timeout must be a positive number"):
            parse_options(["--timeout", "abc"])

    def test_timeout_zero(self):
        with pytest.raises(ValueError, match="--timeout must be a positive number"):
            parse_options(["--timeout", "0"])

    def test_timeout_negative(self):
        with pytest.raises(ValueError, match="--timeout must be a positive number"):
            parse_options(["--timeout", "-5"])


class TestRunnerFlag:
    def test_runner_pytest(self):
        opts = parse_options(["--runner", "pytest"])
        assert opts.runner == "pytest"

    def test_runner_unittest(self):
        opts = parse_options(["--runner", "unittest"])
        assert opts.runner == "unittest"

    def test_runner_invalid(self):
        with pytest.raises(ValueError, match="Invalid runner"):
            parse_options(["--runner", "nose"])

    def test_runner_missing_value(self):
        with pytest.raises(ValueError, match="--runner requires a value"):
            parse_options(["--runner"])


class TestCoverageCommandFlag:
    def test_coverage_command(self):
        opts = parse_options(["--coverage-command", "coverage run -m pytest"])
        assert opts.coverage_command == "coverage run -m pytest"

    def test_coverage_command_missing_value(self):
        with pytest.raises(ValueError, match="--coverage-command requires a value"):
            parse_options(["--coverage-command"])


class TestExcludeFlag:
    def test_single_exclude(self):
        opts = parse_options(["--exclude", "test_*"])
        assert opts.excludes == ["test_*"]

    def test_multiple_excludes(self):
        opts = parse_options(["--exclude", "test_*", "--exclude", "vendor/*"])
        assert opts.excludes == ["test_*", "vendor/*"]

    def test_exclude_missing_value(self):
        with pytest.raises(ValueError, match="--exclude requires a value"):
            parse_options(["--exclude"])


class TestFailOnCrapFlag:
    def test_fail_on_crap(self):
        opts = parse_options(["--fail-on-crap", "30"])
        assert opts.fail_on_crap == 30.0

    def test_fail_on_crap_float(self):
        opts = parse_options(["--fail-on-crap", "15.5"])
        assert opts.fail_on_crap == 15.5

    def test_fail_on_crap_missing_value(self):
        with pytest.raises(ValueError, match="--fail-on-crap requires a value"):
            parse_options(["--fail-on-crap"])

    def test_fail_on_crap_not_a_number(self):
        with pytest.raises(ValueError, match="--fail-on-crap must be a positive number"):
            parse_options(["--fail-on-crap", "abc"])

    def test_fail_on_crap_zero(self):
        with pytest.raises(ValueError, match="--fail-on-crap must be a positive number"):
            parse_options(["--fail-on-crap", "0"])

    def test_fail_on_crap_negative(self):
        with pytest.raises(ValueError, match="--fail-on-crap must be a positive number"):
            parse_options(["--fail-on-crap", "-1"])


class TestFailOnComplexityFlag:
    def test_fail_on_complexity(self):
        opts = parse_options(["--fail-on-complexity", "10"])
        assert opts.fail_on_complexity == 10.0

    def test_fail_on_complexity_float(self):
        opts = parse_options(["--fail-on-complexity", "5.5"])
        assert opts.fail_on_complexity == 5.5

    def test_fail_on_complexity_missing_value(self):
        with pytest.raises(ValueError, match="--fail-on-complexity requires a value"):
            parse_options(["--fail-on-complexity"])

    def test_fail_on_complexity_not_a_number(self):
        with pytest.raises(ValueError, match="--fail-on-complexity must be a positive number"):
            parse_options(["--fail-on-complexity", "abc"])

    def test_fail_on_complexity_zero(self):
        with pytest.raises(ValueError, match="--fail-on-complexity must be a positive number"):
            parse_options(["--fail-on-complexity", "0"])

    def test_fail_on_complexity_negative(self):
        with pytest.raises(ValueError, match="--fail-on-complexity must be a positive number"):
            parse_options(["--fail-on-complexity", "-1"])


class TestFailOnCoverageBelowFlag:
    def test_fail_on_coverage_below(self):
        opts = parse_options(["--fail-on-coverage-below", "80"])
        assert opts.fail_on_coverage_below == 80.0

    def test_fail_on_coverage_below_zero(self):
        opts = parse_options(["--fail-on-coverage-below", "0"])
        assert opts.fail_on_coverage_below == 0.0

    def test_fail_on_coverage_below_hundred(self):
        opts = parse_options(["--fail-on-coverage-below", "100"])
        assert opts.fail_on_coverage_below == 100.0

    def test_fail_on_coverage_below_float(self):
        opts = parse_options(["--fail-on-coverage-below", "75.5"])
        assert opts.fail_on_coverage_below == 75.5

    def test_fail_on_coverage_below_missing_value(self):
        with pytest.raises(ValueError, match="--fail-on-coverage-below requires a value"):
            parse_options(["--fail-on-coverage-below"])

    def test_fail_on_coverage_below_not_a_number(self):
        with pytest.raises(ValueError, match="--fail-on-coverage-below must be a number between 0 and 100"):
            parse_options(["--fail-on-coverage-below", "abc"])

    def test_fail_on_coverage_below_negative(self):
        with pytest.raises(ValueError, match="--fail-on-coverage-below must be a number between 0 and 100"):
            parse_options(["--fail-on-coverage-below", "-1"])

    def test_fail_on_coverage_below_over_hundred(self):
        with pytest.raises(ValueError, match="--fail-on-coverage-below must be a number between 0 and 100"):
            parse_options(["--fail-on-coverage-below", "101"])


class TestTopFlag:
    def test_top(self):
        opts = parse_options(["--top", "10"])
        assert opts.top == 10

    def test_top_missing_value(self):
        with pytest.raises(ValueError, match="--top requires a value"):
            parse_options(["--top"])

    def test_top_not_a_number(self):
        with pytest.raises(ValueError, match="--top must be a positive integer"):
            parse_options(["--top", "abc"])

    def test_top_zero(self):
        with pytest.raises(ValueError, match="--top must be a positive integer"):
            parse_options(["--top", "0"])

    def test_top_negative(self):
        with pytest.raises(ValueError, match="--top must be a positive integer"):
            parse_options(["--top", "-1"])

    def test_top_float(self):
        with pytest.raises(ValueError, match="--top must be a positive integer"):
            parse_options(["--top", "3.5"])


class TestConfigFlag:
    def test_config(self):
        opts = parse_options(["--config", "crap4py.toml"])
        assert opts.config_path == "crap4py.toml"

    def test_config_missing_value(self):
        with pytest.raises(ValueError, match="--config requires a value"):
            parse_options(["--config"])


class TestPositionalFilters:
    def test_single_filter(self):
        opts = parse_options(["my_module"])
        assert opts.filters == ["my_module"]

    def test_multiple_filters(self):
        opts = parse_options(["mod_a", "mod_b"])
        assert opts.filters == ["mod_a", "mod_b"]


class TestMixedFlagsAndFilters:
    def test_flags_before_filters(self):
        opts = parse_options(["--src", "lib", "my_module"])
        assert opts.src_dir == "lib"
        assert opts.filters == ["my_module"]

    def test_filters_between_flags(self):
        opts = parse_options(["my_module", "--src", "lib"])
        assert opts.src_dir == "lib"
        assert opts.filters == ["my_module"]

    def test_complex_mix(self):
        opts = parse_options([
            "--src", "lib",
            "--timeout", "60",
            "--exclude", "test_*",
            "--output", "json",
            "--fail-on-crap", "30",
            "--top", "5",
            "mod_a",
            "mod_b",
        ])
        assert opts.src_dir == "lib"
        assert opts.timeout_s == 60
        assert opts.excludes == ["test_*"]
        assert opts.output == "json"
        assert opts.fail_on_crap == 30.0
        assert opts.top == 5
        assert opts.filters == ["mod_a", "mod_b"]
        assert opts.mode == "report"


class TestUnknownFlags:
    def test_unknown_flag(self):
        with pytest.raises(ValueError, match="Unknown option"):
            parse_options(["--unknown"])
