import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from crap4py.skill_cmd import (
    _SKILL_FILE,
    _copy_skill,
    run_skill_cmd,
)


class TestSkillFileExists:
    def test_bundled_skill_exists(self):
        assert _SKILL_FILE.exists()

    def test_bundled_skill_has_frontmatter(self):
        content = _SKILL_FILE.read_text()
        assert content.startswith("---")
        assert "name: crap4py" in content
        assert "description:" in content


class TestCopySkill:
    def test_copies_skill_to_target(self, tmp_path):
        target = tmp_path / "crap4py"
        _copy_skill(target)

        skill_file = target / "SKILL.md"
        assert skill_file.exists()
        assert skill_file.read_text() == _SKILL_FILE.read_text()

    def test_creates_parent_dirs(self, tmp_path):
        target = tmp_path / "deep" / "nested" / "crap4py"
        _copy_skill(target)
        assert (target / "SKILL.md").exists()

    def test_overwrites_existing(self, tmp_path):
        target = tmp_path / "crap4py"
        target.mkdir()
        (target / "SKILL.md").write_text("old content")

        _copy_skill(target)
        assert (target / "SKILL.md").read_text() == _SKILL_FILE.read_text()


class TestInstall:
    def test_install_global(self, tmp_path, capsys):
        target = tmp_path / ".agents" / "skills" / "crap4py"
        with patch("crap4py.skill_cmd._GLOBAL_TARGET", target):
            run_skill_cmd(["install"])

        assert (target / "SKILL.md").exists()
        out = capsys.readouterr().out
        assert "global" in out
        assert "Installed" in out

    def test_install_project(self, tmp_path, capsys, monkeypatch):
        monkeypatch.chdir(tmp_path)
        target = tmp_path / ".agents" / "skills" / "crap4py"
        with patch("crap4py.skill_cmd._PROJECT_TARGET", target):
            run_skill_cmd(["install", "--project"])

        assert (target / "SKILL.md").exists()
        out = capsys.readouterr().out
        assert "project" in out
        assert "Installed" in out


class TestUninstall:
    def test_uninstall_global(self, tmp_path, capsys):
        target = tmp_path / ".agents" / "skills" / "crap4py"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("skill content")

        with patch("crap4py.skill_cmd._GLOBAL_TARGET", target), \
             patch("crap4py.skill_cmd._PROJECT_TARGET", tmp_path / "nonexistent"):
            run_skill_cmd(["uninstall"])

        assert not (target / "SKILL.md").exists()
        out = capsys.readouterr().out
        assert "Removed" in out

    def test_uninstall_project(self, tmp_path, capsys):
        target = tmp_path / ".agents" / "skills" / "crap4py"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("skill content")

        with patch("crap4py.skill_cmd._GLOBAL_TARGET", tmp_path / "nonexistent"), \
             patch("crap4py.skill_cmd._PROJECT_TARGET", target):
            run_skill_cmd(["uninstall"])

        assert not (target / "SKILL.md").exists()
        out = capsys.readouterr().out
        assert "Removed" in out

    def test_uninstall_not_installed(self, tmp_path, capsys):
        with patch("crap4py.skill_cmd._GLOBAL_TARGET", tmp_path / "nonexistent"), \
             patch("crap4py.skill_cmd._PROJECT_TARGET", tmp_path / "also_nonexistent"):
            run_skill_cmd(["uninstall"])

        out = capsys.readouterr().out
        assert "No installed skill found" in out


class TestShow:
    def test_show_prints_skill(self, capsys):
        run_skill_cmd(["show"])
        out = capsys.readouterr().out
        assert "name: crap4py" in out
        assert "CRAP" in out


class TestPath:
    def test_path_when_installed(self, tmp_path, capsys):
        target = tmp_path / ".agents" / "skills" / "crap4py"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("content")

        with patch("crap4py.skill_cmd._GLOBAL_TARGET", target):
            run_skill_cmd(["path"])

        out = capsys.readouterr().out
        assert "SKILL.md" in out

    def test_path_when_not_installed(self, tmp_path):
        with patch("crap4py.skill_cmd._GLOBAL_TARGET", tmp_path / "nope"), \
             patch("crap4py.skill_cmd._PROJECT_TARGET", tmp_path / "also_nope"):
            with pytest.raises(SystemExit) as exc:
                run_skill_cmd(["path"])
            assert exc.value.code == 1


class TestUsage:
    def test_no_args_shows_usage(self, capsys):
        with pytest.raises(SystemExit):
            run_skill_cmd([])
        out = capsys.readouterr().out
        assert "Usage:" in out

    def test_unknown_command_shows_usage(self, capsys):
        with pytest.raises(SystemExit):
            run_skill_cmd(["banana"])
        out = capsys.readouterr().out
        assert "Unknown skill command" in out
        assert "Usage:" in out


class TestMainRouting:
    """Test that __main__.py routes 'skill' subcommand correctly."""

    @patch("crap4py.__main__.sys.argv", ["crap4py", "skill", "show"])
    def test_skill_subcommand_routes(self, capsys):
        from crap4py.__main__ import main
        main()
        out = capsys.readouterr().out
        assert "name: crap4py" in out
