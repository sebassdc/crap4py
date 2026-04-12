import sys
from unittest.mock import patch, MagicMock

import pytest

from crap4py.__main__ import main
from crap4py.options import CliOptions


class TestMainHelp:
    @patch.object(sys, "argv", ["crap4py", "--help"])
    def test_help_flag_prints_usage(self, capsys):
        main()
        out = capsys.readouterr().out
        assert "Usage:" in out
        assert "--src" in out
        assert "--help" in out

    @patch.object(sys, "argv", ["crap4py", "-h"])
    def test_short_help_flag(self, capsys):
        main()
        out = capsys.readouterr().out
        assert "Usage:" in out


class TestMainVersion:
    @patch.object(sys, "argv", ["crap4py", "--version"])
    @patch("crap4py.__main__.pkg_version", side_effect=Exception("not installed"))
    def test_version_fallback(self, mock_pkg, capsys):
        main()
        out = capsys.readouterr().out.strip()
        assert "0.1.0" in out

    @patch.object(sys, "argv", ["crap4py", "-v"])
    @patch("crap4py.__main__.pkg_version", return_value="1.2.3")
    def test_version_from_metadata(self, mock_pkg, capsys):
        main()
        out = capsys.readouterr().out.strip()
        assert out == "1.2.3"


class TestMainSkill:
    @patch("crap4py.__main__._handle_skill_command", return_value=True)
    def test_skill_command_intercepted(self, mock_skill):
        main()
        mock_skill.assert_called_once()

    @patch("crap4py.__main__._handle_skill_command", return_value=True)
    @patch("crap4py.__main__.run_report")
    def test_skill_command_prevents_report(self, mock_report, mock_skill):
        main()
        mock_report.assert_not_called()


class TestMainReport:
    @patch.object(sys, "argv", ["crap4py"])
    @patch("crap4py.__main__.load_config", return_value={})
    @patch("crap4py.__main__.merge_config_into_options", side_effect=lambda opts, cfg: opts)
    @patch("crap4py.__main__.run_report", return_value=0)
    def test_default_args_calls_run_report(self, mock_report, mock_merge, mock_config):
        main()
        mock_report.assert_called_once()

    @patch.object(sys, "argv", ["crap4py", "--src", "lib", "--json", "parser"])
    @patch("crap4py.__main__.load_config", return_value={})
    @patch("crap4py.__main__.merge_config_into_options", side_effect=lambda opts, cfg: opts)
    @patch("crap4py.__main__.run_report", return_value=0)
    def test_options_forwarded_to_report(self, mock_report, mock_merge, mock_config):
        main()
        opts = mock_report.call_args[0][0]
        assert opts.src_dir == "lib"
        assert opts.output == "json"
        assert opts.filters == ["parser"]

    @patch.object(sys, "argv", ["crap4py"])
    @patch("crap4py.__main__.load_config", return_value={})
    @patch("crap4py.__main__.merge_config_into_options", side_effect=lambda opts, cfg: opts)
    @patch("crap4py.__main__.run_report", return_value=1)
    def test_nonzero_exit_code_calls_sys_exit(self, mock_report, mock_merge, mock_config):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    @patch.object(sys, "argv", ["crap4py"])
    @patch("crap4py.__main__.load_config", return_value={})
    @patch("crap4py.__main__.merge_config_into_options", side_effect=lambda opts, cfg: opts)
    @patch("crap4py.__main__.run_report", return_value=0)
    def test_zero_exit_does_not_call_sys_exit(self, mock_report, mock_merge, mock_config):
        # Should not raise
        main()


class TestMainInvalidOption:
    @patch.object(sys, "argv", ["crap4py", "--output", "invalid"])
    def test_invalid_output_format_exits_2(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 2
        err = capsys.readouterr().err
        assert "Invalid output format" in err

    @patch.object(sys, "argv", ["crap4py", "--unknown-flag"])
    def test_unknown_flag_exits_2(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 2
        err = capsys.readouterr().err
        assert "Unknown option" in err


class TestMainConfig:
    @patch.object(sys, "argv", ["crap4py"])
    @patch("crap4py.__main__.run_report", return_value=0)
    @patch("crap4py.__main__.load_config", return_value={"src": "lib"})
    def test_config_merged_into_options(self, mock_config, mock_report):
        main()
        merged_opts = mock_report.call_args[0][0]
        # Config should override the default "src" -> "lib"
        assert merged_opts.src_dir == "lib"

    @patch.object(sys, "argv", ["crap4py", "--src", "custom"])
    @patch("crap4py.__main__.run_report", return_value=0)
    @patch("crap4py.__main__.load_config", return_value={"src": "lib"})
    def test_cli_takes_precedence_over_config(self, mock_config, mock_report):
        main()
        merged_opts = mock_report.call_args[0][0]
        # CLI --src custom should win over config src=lib
        assert merged_opts.src_dir == "custom"

    @patch.object(sys, "argv", ["crap4py", "--config", "/tmp/my.json"])
    @patch("crap4py.__main__.run_report", return_value=0)
    @patch("crap4py.__main__.load_config", return_value={})
    def test_explicit_config_path_forwarded(self, mock_config, mock_report):
        main()
        mock_config.assert_called_once_with("/tmp/my.json")
