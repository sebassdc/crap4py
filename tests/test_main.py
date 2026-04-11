import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

from crap4py.__main__ import main
from crap4py.models import CrapEntry


FAKE_ENTRIES = [CrapEntry(name="foo", module="bar", complexity=1, coverage=100.0, crap=1.0)]


def _make_run(returncode=0):
    result = MagicMock()
    result.returncode = returncode
    return result


@patch("crap4py.__main__.format_report", return_value="REPORT")
@patch("crap4py.__main__.sort_by_crap", return_value=FAKE_ENTRIES)
@patch("crap4py.__main__.analyze_file", return_value=FAKE_ENTRIES)
@patch("crap4py.__main__.parse_coverage", return_value={})
@patch("crap4py.__main__.filter_sources", side_effect=lambda s, f: s)
@patch("crap4py.__main__.find_source_files", return_value=["src/crap4py/core.py"])
@patch("crap4py.__main__.subprocess.run", return_value=_make_run(0))
@patch("crap4py.__main__.os.path.exists", return_value=False)
def test_happy_path_no_stale_files(mock_exists, mock_run, mock_find, mock_filter,
                                    mock_parse, mock_analyze, mock_sort, mock_fmt, capsys):
    main()

    mock_exists.assert_any_call(".coverage")
    mock_exists.assert_any_call("coverage.json")
    assert mock_run.call_count == 2
    out = capsys.readouterr().out
    assert "REPORT" in out


@patch("crap4py.__main__.format_report", return_value="REPORT")
@patch("crap4py.__main__.sort_by_crap", return_value=FAKE_ENTRIES)
@patch("crap4py.__main__.analyze_file", return_value=FAKE_ENTRIES)
@patch("crap4py.__main__.parse_coverage", return_value={})
@patch("crap4py.__main__.filter_sources", side_effect=lambda s, f: s)
@patch("crap4py.__main__.find_source_files", return_value=["src/crap4py/core.py"])
@patch("crap4py.__main__.subprocess.run", return_value=_make_run(0))
@patch("crap4py.__main__.os.remove")
@patch("crap4py.__main__.os.path.exists", return_value=True)
def test_stale_files_are_deleted(mock_exists, mock_remove, mock_run, mock_find,
                                  mock_filter, mock_parse, mock_analyze, mock_sort, mock_fmt):
    main()

    mock_remove.assert_any_call(".coverage")
    mock_remove.assert_any_call("coverage.json")


@patch("crap4py.__main__.sys.exit", side_effect=SystemExit(1))
@patch("crap4py.__main__.subprocess.run", return_value=_make_run(1))
@patch("crap4py.__main__.os.path.exists", return_value=False)
def test_coverage_run_failure_exits(mock_exists, mock_run, mock_exit, capsys):
    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 1
    mock_exit.assert_called_once_with(1)
    out = capsys.readouterr().out
    assert "Coverage failed" in out
    assert "1" in out


@patch("crap4py.__main__.sys.exit", side_effect=SystemExit(1))
@patch("crap4py.__main__.subprocess.run", side_effect=[_make_run(0), _make_run(2)])
@patch("crap4py.__main__.os.path.exists", return_value=False)
def test_coverage_json_failure_exits(mock_exists, mock_run, mock_exit, capsys):
    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 1
    mock_exit.assert_called_once_with(1)
    out = capsys.readouterr().out
    assert "coverage json failed" in out
    assert "2" in out


@patch("crap4py.__main__.format_report", return_value="REPORT")
@patch("crap4py.__main__.sort_by_crap", return_value=FAKE_ENTRIES)
@patch("crap4py.__main__.analyze_file", return_value=FAKE_ENTRIES)
@patch("crap4py.__main__.parse_coverage", return_value={})
@patch("crap4py.__main__.filter_sources", side_effect=lambda s, f: s)
@patch("crap4py.__main__.find_source_files", return_value=["src/crap4py/core.py"])
@patch("crap4py.__main__.subprocess.run", return_value=_make_run(0))
@patch("crap4py.__main__.os.path.exists", return_value=False)
def test_argv_filters_forwarded(mock_exists, mock_run, mock_find, mock_filter,
                                 mock_parse, mock_analyze, mock_sort, mock_fmt):
    with patch.object(sys, "argv", ["crap4py", "complexity", "core"]):
        main()

    mock_filter.assert_called_once_with(["src/crap4py/core.py"], ["complexity", "core"])


@patch("crap4py.__main__.sys.exit", side_effect=SystemExit(1))
@patch("crap4py.__main__.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="test", timeout=300))
@patch("crap4py.__main__.os.path.exists", return_value=False)
def test_coverage_run_timeout_exits(mock_exists, mock_run, mock_exit, capsys):
    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 1
    mock_exit.assert_called_once_with(1)
    out = capsys.readouterr().out
    assert "coverage run timed out" in out


@patch("crap4py.__main__.sys.exit", side_effect=SystemExit(1))
@patch("crap4py.__main__.subprocess.run", side_effect=[_make_run(0), subprocess.TimeoutExpired(cmd="test", timeout=300)])
@patch("crap4py.__main__.os.path.exists", return_value=False)
def test_coverage_json_timeout_exits(mock_exists, mock_run, mock_exit, capsys):
    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 1
    mock_exit.assert_called_once_with(1)
    out = capsys.readouterr().out
    assert "coverage json timed out" in out
