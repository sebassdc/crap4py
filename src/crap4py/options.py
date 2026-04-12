"""CLI argument parsing for crap4py."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CliOptions:
    mode: str = "report"  # "report" | "help" | "version"
    filters: List[str] = field(default_factory=list)
    src_dir: str = "src"
    timeout_s: int = 300
    output: str = "text"  # "text" | "json" | "markdown" | "csv"
    excludes: List[str] = field(default_factory=list)
    runner: Optional[str] = None  # "pytest" | "unittest"
    coverage_command: Optional[str] = None
    fail_on_crap: Optional[float] = None
    fail_on_complexity: Optional[float] = None
    fail_on_coverage_below: Optional[float] = None
    top: Optional[int] = None
    config_path: Optional[str] = None


_VALID_OUTPUTS = {"text", "json", "markdown", "csv"}
_VALID_RUNNERS = {"pytest", "unittest"}

# Simple flags that set a field to a fixed value (no argument consumed)
_SIMPLE_FLAGS = {
    "--help": ("mode", "help"),
    "-h": ("mode", "help"),
    "--version": ("mode", "version"),
    "-v": ("mode", "version"),
    "--json": ("output", "json"),
}


def _consume_value(argv: list, i: int, flag: str) -> str:
    """Return the next argument as the value for flag, or raise if missing."""
    if i + 1 >= len(argv):
        raise ValueError(f"{flag} requires a value")
    return argv[i + 1]


def _parse_positive_float(value: str, flag: str) -> float:
    try:
        n = float(value)
    except ValueError:
        raise ValueError(f"{flag} must be a positive number")
    if n <= 0:
        raise ValueError(f"{flag} must be a positive number")
    return n


def _parse_positive_int(value: str, flag: str) -> int:
    try:
        n = int(value)
        # Reject strings that look like floats
        if str(n) != value:
            raise ValueError()
    except ValueError:
        raise ValueError(f"{flag} must be a positive integer")
    if n <= 0:
        raise ValueError(f"{flag} must be a positive integer")
    return n


def _apply_validated_choice(opts, value, field, valid_set, label):
    if value not in valid_set:
        raise ValueError(
            f"Invalid {label} '{value}'. Must be one of: {', '.join(sorted(valid_set))}"
        )
    setattr(opts, field, value)


def _apply_timeout(opts, value):
    try:
        n = int(value)
        if str(n) != value:
            raise ValueError()
    except ValueError:
        raise ValueError("--timeout must be a positive number")
    if n <= 0:
        raise ValueError("--timeout must be a positive number")
    opts.timeout_s = n


def _apply_coverage_below(opts, value):
    try:
        n = float(value)
    except ValueError:
        raise ValueError(
            "--fail-on-coverage-below must be a number between 0 and 100"
        )
    if n < 0 or n > 100:
        raise ValueError(
            "--fail-on-coverage-below must be a number between 0 and 100"
        )
    opts.fail_on_coverage_below = n


# Handlers for flags that consume the next argument: flag -> (opts, value) -> None
_FLAG_HANDLERS = {
    "--output": lambda opts, val: _apply_validated_choice(
        opts, val, "output", _VALID_OUTPUTS, "output format",
    ),
    "--src": lambda opts, val: setattr(opts, "src_dir", val),
    "--timeout": _apply_timeout,
    "--runner": lambda opts, val: _apply_validated_choice(
        opts, val, "runner", _VALID_RUNNERS, "runner",
    ),
    "--coverage-command": lambda opts, val: setattr(opts, "coverage_command", val),
    "--exclude": lambda opts, val: opts.excludes.append(val),
    "--fail-on-crap": lambda opts, val: setattr(
        opts, "fail_on_crap", _parse_positive_float(val, "--fail-on-crap"),
    ),
    "--fail-on-complexity": lambda opts, val: setattr(
        opts, "fail_on_complexity", _parse_positive_float(val, "--fail-on-complexity"),
    ),
    "--fail-on-coverage-below": _apply_coverage_below,
    "--top": lambda opts, val: setattr(
        opts, "top", _parse_positive_int(val, "--top"),
    ),
    "--config": lambda opts, val: setattr(opts, "config_path", val),
}


def parse_options(argv: list) -> CliOptions:
    """Parse CLI arguments into a CliOptions instance.

    Args:
        argv: List of command-line arguments (without the program name).

    Returns:
        A populated CliOptions dataclass.

    Raises:
        ValueError: If any argument is invalid.
    """
    opts = CliOptions()
    i = 0

    while i < len(argv):
        arg = argv[i]

        if arg in _SIMPLE_FLAGS:
            field, value = _SIMPLE_FLAGS[arg]
            setattr(opts, field, value)
            i += 1
        elif arg in _FLAG_HANDLERS:
            val = _consume_value(argv, i, arg)
            _FLAG_HANDLERS[arg](opts, val)
            i += 2
        elif arg.startswith("-"):
            raise ValueError(f"Unknown option: {arg}")
        else:
            opts.filters.append(arg)
            i += 1

    return opts
