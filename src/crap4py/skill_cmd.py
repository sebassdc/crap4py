"""Manage the crap4py agent skill (install, uninstall, show)."""

import os
import shutil
import sys
from pathlib import Path

# The SKILL.md bundled inside the package
_SKILL_DIR = Path(__file__).parent / "skill"
_SKILL_FILE = _SKILL_DIR / "SKILL.md"

# Cross-agent standard locations
_GLOBAL_TARGET = Path.home() / ".agents" / "skills" / "crap4py"
_PROJECT_TARGET = Path(".agents") / "skills" / "crap4py"

USAGE = """\
Usage: crap4py skill <command>

Commands:
  install            Install skill to ~/.agents/skills/crap4py/ (all agents)
  install --project  Install skill to .agents/skills/crap4py/ (this project)
  uninstall          Remove skill from ~/.agents/skills/crap4py/
  show               Print the SKILL.md to stdout
  path               Print the installed skill path
"""


def _copy_skill(target: Path) -> None:
    """Copy the bundled skill directory to target."""
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_SKILL_FILE, target / "SKILL.md")


def _install(project: bool = False) -> None:
    target = _PROJECT_TARGET if project else _GLOBAL_TARGET
    _copy_skill(target)
    scope = "project" if project else "global"
    print(f"Installed crap4py skill ({scope}): {target / 'SKILL.md'}")


def _uninstall() -> None:
    for target in (_GLOBAL_TARGET, _PROJECT_TARGET):
        skill_file = target / "SKILL.md"
        if skill_file.exists():
            skill_file.unlink()
            # Remove the directory if empty
            try:
                target.rmdir()
            except OSError:
                pass
            print(f"Removed: {skill_file}")
            return
    print("No installed skill found.")


def _show() -> None:
    print(_SKILL_FILE.read_text())


def _path() -> None:
    for target in (_GLOBAL_TARGET, _PROJECT_TARGET):
        skill_file = target / "SKILL.md"
        if skill_file.exists():
            print(skill_file)
            return
    print("Not installed. Run: crap4py skill install")
    sys.exit(1)


def run_skill_cmd(args: list[str]) -> None:
    """Dispatch the skill subcommand."""
    if not args:
        print(USAGE)
        sys.exit(1)

    cmd = args[0]

    if cmd == "install":
        project = "--project" in args
        _install(project=project)
    elif cmd == "uninstall":
        _uninstall()
    elif cmd == "show":
        _show()
    elif cmd == "path":
        _path()
    else:
        print(f"Unknown skill command: {cmd}\n")
        print(USAGE)
        sys.exit(1)
