"""Tests for crap4py.report — orchestration, runner detection, and thresholds."""

from unittest.mock import patch, MagicMock, call
import subprocess

import pytest

from crap4py.models import CrapEntry
from crap4py.options import CliOptions
from crap4py.report import detect_runner, evaluate_thresholds, run_report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(name="fn", module="mod", complexity=5, coverage=80.0, crap=6.2):
    return CrapEntry(name=name, module=module, complexity=complexity, coverage=coverage, crap=crap)


# ---------------------------------------------------------------------------
# TestDetectRunner
# ---------------------------------------------------------------------------

class TestDetectRunner:
    def test_defaults_to_pytest(self):
        assert detect_runner() == "pytest"


# ---------------------------------------------------------------------------
# TestEvaluateThresholds
# ---------------------------------------------------------------------------

class TestEvaluateThresholds:
    def test_no_thresholds_returns_none(self):
        opts = CliOptions()
        entries = [_entry(crap=20.0)]
        assert evaluate_thresholds(entries, opts) is None

    def test_crap_threshold_fails(self):
        opts = CliOptions(fail_on_crap=10.0)
        entries = [_entry(crap=12.0), _entry(crap=5.0)]
        msg = evaluate_thresholds(entries, opts)
        assert msg is not None
        assert "CRAP threshold" in msg
        assert "1 function(s)" in msg

    def test_crap_threshold_passes(self):
        opts = CliOptions(fail_on_crap=20.0)
        entries = [_entry(crap=5.0)]
        assert evaluate_thresholds(entries, opts) is None

    def test_complexity_threshold_fails(self):
        opts = CliOptions(fail_on_complexity=3.0)
        entries = [_entry(complexity=5), _entry(complexity=10)]
        msg = evaluate_thresholds(entries, opts)
        assert msg is not None
        assert "complexity threshold" in msg
        assert "2 function(s)" in msg

    def test_complexity_threshold_passes(self):
        opts = CliOptions(fail_on_complexity=10.0)
        entries = [_entry(complexity=5)]
        assert evaluate_thresholds(entries, opts) is None

    def test_coverage_below_threshold_fails(self):
        opts = CliOptions(fail_on_coverage_below=90.0)
        entries = [_entry(coverage=80.0), _entry(coverage=95.0)]
        msg = evaluate_thresholds(entries, opts)
        assert msg is not None
        assert "coverage threshold" in msg
        assert "1 function(s)" in msg

    def test_coverage_below_threshold_passes(self):
        opts = CliOptions(fail_on_coverage_below=50.0)
        entries = [_entry(coverage=80.0)]
        assert evaluate_thresholds(entries, opts) is None

    def test_crap_threshold_boundary_equal(self):
        """Entry with crap == threshold should fail (>= check)."""
        opts = CliOptions(fail_on_crap=10.0)
        entries = [_entry(crap=10.0)]
        msg = evaluate_thresholds(entries, opts)
        assert msg is not None

    def test_complexity_threshold_boundary_equal(self):
        """Entry with complexity == threshold should fail (>= check)."""
        opts = CliOptions(fail_on_complexity=5.0)
        entries = [_entry(complexity=5)]
        msg = evaluate_thresholds(entries, opts)
        assert msg is not None

    def test_coverage_below_boundary_equal(self):
        """Entry with coverage == threshold should pass (not below)."""
        opts = CliOptions(fail_on_coverage_below=80.0)
        entries = [_entry(coverage=80.0)]
        assert evaluate_thresholds(entries, opts) is None


# ---------------------------------------------------------------------------
# TestRunReport
# ---------------------------------------------------------------------------

class TestRunReport:
    def test_missing_src_dir_returns_1(self, capsys):
        opts = CliOptions(src_dir="/nonexistent/path/abc123")
        code = run_report(opts)
        assert code == 1
        assert "does not exist" in capsys.readouterr().err

    @patch("crap4py.report.find_source_files_with_options", return_value=[])
    def test_no_files_found_returns_1(self, mock_find, capsys, tmp_path):
        opts = CliOptions(src_dir=str(tmp_path))
        code = run_report(opts)
        assert code == 1
        assert "No Python files found" in capsys.readouterr().err

    @patch("crap4py.report.filter_sources", return_value=[])
    @patch("crap4py.report.find_source_files_with_options", return_value=["src/a.py"])
    def test_no_filter_matches_returns_1(self, mock_find, mock_filter, capsys, tmp_path):
        opts = CliOptions(src_dir=str(tmp_path), filters=["nonexistent"])
        code = run_report(opts)
        assert code == 1
        assert "No files match the filters" in capsys.readouterr().err

    @patch("crap4py.report._run_coverage_step", return_value=True)
    @patch("crap4py.report.parse_coverage", return_value={})
    @patch("crap4py.report.analyze_file", return_value=[_entry()])
    @patch("crap4py.report.filter_sources", return_value=["src/mod.py"])
    @patch("crap4py.report.find_source_files_with_options", return_value=["src/mod.py"])
    def test_successful_text_output(self, mock_find, mock_filter, mock_analyze, mock_cov, mock_run, capsys, tmp_path):
        opts = CliOptions(src_dir=str(tmp_path), output="text")
        code = run_report(opts)
        assert code == 0
        out = capsys.readouterr().out
        assert "CRAP Report" in out

    @patch("crap4py.report._run_coverage_step", return_value=True)
    @patch("crap4py.report.parse_coverage", return_value={})
    @patch("crap4py.report.analyze_file", return_value=[_entry()])
    @patch("crap4py.report.filter_sources", return_value=["src/mod.py"])
    @patch("crap4py.report.find_source_files_with_options", return_value=["src/mod.py"])
    def test_json_output(self, mock_find, mock_filter, mock_analyze, mock_cov, mock_run, capsys, tmp_path):
        opts = CliOptions(src_dir=str(tmp_path), output="json")
        code = run_report(opts)
        assert code == 0
        out = capsys.readouterr().out
        assert '"tool": "crap4py"' in out

    @patch("crap4py.report._run_coverage_step", return_value=True)
    @patch("crap4py.report.parse_coverage", return_value={})
    @patch("crap4py.report.analyze_file")
    @patch("crap4py.report.filter_sources", return_value=["src/a.py", "src/b.py"])
    @patch("crap4py.report.find_source_files_with_options", return_value=["src/a.py", "src/b.py"])
    def test_top_limits_displayed_entries(self, mock_find, mock_filter, mock_analyze, mock_cov, mock_run, capsys, tmp_path):
        mock_analyze.side_effect = [
            [_entry(name="high", crap=50.0)],
            [_entry(name="low", crap=2.0)],
        ]
        opts = CliOptions(src_dir=str(tmp_path), output="text", top=1)
        code = run_report(opts)
        assert code == 0
        out = capsys.readouterr().out
        assert "high" in out
        assert "low" not in out

    @patch("crap4py.report._run_coverage_step", return_value=True)
    @patch("crap4py.report.parse_coverage", return_value={})
    @patch("crap4py.report.analyze_file", return_value=[_entry(crap=25.0)])
    @patch("crap4py.report.filter_sources", return_value=["src/mod.py"])
    @patch("crap4py.report.find_source_files_with_options", return_value=["src/mod.py"])
    def test_threshold_failure_returns_1_but_still_prints_report(self, mock_find, mock_filter, mock_analyze, mock_cov, mock_run, capsys, tmp_path):
        opts = CliOptions(src_dir=str(tmp_path), output="text", fail_on_crap=10.0)
        code = run_report(opts)
        assert code == 1
        captured = capsys.readouterr()
        assert "CRAP Report" in captured.out
        assert "CRAP threshold" in captured.err

    @patch("crap4py.report._run_coverage_step", return_value=False)
    @patch("crap4py.report.filter_sources", return_value=["src/mod.py"])
    @patch("crap4py.report.find_source_files_with_options", return_value=["src/mod.py"])
    def test_coverage_failure_returns_1(self, mock_find, mock_filter, mock_run, tmp_path):
        opts = CliOptions(src_dir=str(tmp_path))
        code = run_report(opts)
        assert code == 1

    @patch("crap4py.report._run_coverage_step", return_value=True)
    @patch("crap4py.report.parse_coverage", return_value={})
    @patch("crap4py.report.analyze_file", return_value=[_entry()])
    @patch("crap4py.report.filter_sources", return_value=["src/mod.py"])
    @patch("crap4py.report.find_source_files_with_options", return_value=["src/mod.py"])
    def test_markdown_output(self, mock_find, mock_filter, mock_analyze, mock_cov, mock_run, capsys, tmp_path):
        opts = CliOptions(src_dir=str(tmp_path), output="markdown")
        code = run_report(opts)
        assert code == 0
        out = capsys.readouterr().out
        assert "# CRAP Report" in out

    @patch("crap4py.report._run_coverage_step", return_value=True)
    @patch("crap4py.report.parse_coverage", return_value={})
    @patch("crap4py.report.analyze_file", return_value=[_entry()])
    @patch("crap4py.report.filter_sources", return_value=["src/mod.py"])
    @patch("crap4py.report.find_source_files_with_options", return_value=["src/mod.py"])
    def test_csv_output(self, mock_find, mock_filter, mock_analyze, mock_cov, mock_run, capsys, tmp_path):
        opts = CliOptions(src_dir=str(tmp_path), output="csv")
        code = run_report(opts)
        assert code == 0
        out = capsys.readouterr().out
        assert "Function,Module,CC,Coverage,CRAP" in out
