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

# Flags that consume the next argument
_VALUE_FLAGS = {
    "--output",
    "--src",
    "--timeout",
    "--runner",
    "--coverage-command",
    "--exclude",
    "--fail-on-crap",
    "--fail-on-complexity",
    "--fail-on-coverage-below",
    "--top",
    "--config",
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

        if arg in ("--help", "-h"):
            opts.mode = "help"
            i += 1
        elif arg in ("--version", "-v"):
            opts.mode = "version"
            i += 1
        elif arg == "--json":
            opts.output = "json"
            i += 1
        elif arg == "--output":
            val = _consume_value(argv, i, "--output")
            if val not in _VALID_OUTPUTS:
                raise ValueError(
                    f"Invalid output format '{val}'. Must be one of: {', '.join(sorted(_VALID_OUTPUTS))}"
                )
            opts.output = val
            i += 2
        elif arg == "--src":
            opts.src_dir = _consume_value(argv, i, "--src")
            i += 2
        elif arg == "--timeout":
            val = _consume_value(argv, i, "--timeout")
            try:
                n = int(val)
                if str(n) != val:
                    raise ValueError()
            except ValueError:
                raise ValueError("--timeout must be a positive number")
            if n <= 0:
                raise ValueError("--timeout must be a positive number")
            opts.timeout_s = n
            i += 2
        elif arg == "--runner":
            val = _consume_value(argv, i, "--runner")
            if val not in _VALID_RUNNERS:
                raise ValueError(
                    f"Invalid runner '{val}'. Must be one of: {', '.join(sorted(_VALID_RUNNERS))}"
                )
            opts.runner = val
            i += 2
        elif arg == "--coverage-command":
            opts.coverage_command = _consume_value(argv, i, "--coverage-command")
            i += 2
        elif arg == "--exclude":
            opts.excludes.append(_consume_value(argv, i, "--exclude"))
            i += 2
        elif arg == "--fail-on-crap":
            val = _consume_value(argv, i, "--fail-on-crap")
            opts.fail_on_crap = _parse_positive_float(val, "--fail-on-crap")
            i += 2
        elif arg == "--fail-on-complexity":
            val = _consume_value(argv, i, "--fail-on-complexity")
            opts.fail_on_complexity = _parse_positive_float(val, "--fail-on-complexity")
            i += 2
        elif arg == "--fail-on-coverage-below":
            val = _consume_value(argv, i, "--fail-on-coverage-below")
            try:
                n = float(val)
            except ValueError:
                raise ValueError(
                    f"--fail-on-coverage-below must be a number between 0 and 100"
                )
            if n < 0 or n > 100:
                raise ValueError(
                    f"--fail-on-coverage-below must be a number between 0 and 100"
                )
            opts.fail_on_coverage_below = n
            i += 2
        elif arg == "--top":
            val = _consume_value(argv, i, "--top")
            opts.top = _parse_positive_int(val, "--top")
            i += 2
        elif arg == "--config":
            opts.config_path = _consume_value(argv, i, "--config")
            i += 2
        elif arg.startswith("-"):
            raise ValueError(f"Unknown option: {arg}")
        else:
            # Positional argument = filter
            opts.filters.append(arg)
            i += 1

    return opts
