import sys
from importlib.metadata import version as pkg_version

from crap4py.config import load_config, merge_config_into_options
from crap4py.options import parse_options
from crap4py.report import run_report


def _handle_skill_command():
    if len(sys.argv) > 1 and sys.argv[1] == "skill":
        from crap4py.skill_cmd import run_skill_cmd
        run_skill_cmd(sys.argv[2:])
        return True
    return False


def _format_help():
    return """Usage: crap4py [options] [filters...]

Options:
  --src <dir>              Source directory to analyze (default: src)
  --exclude <pattern>      Exclude files whose path contains <pattern> (repeatable)
  --timeout <seconds>      Analysis timeout in seconds (default: 300)
  --output <format>        Output format: text, json, markdown, csv (default: text)
  --json                   Shorthand for --output json
  --runner <pytest|unittest>  Skip auto-detection, use specified test runner
  --coverage-command <cmd> Run a custom shell command for coverage instead
  --fail-on-crap <n>       Exit 1 if any function CRAP score >= n
  --fail-on-complexity <n> Exit 1 if any function complexity >= n
  --fail-on-coverage-below <n>  Exit 1 if any function coverage < n (0-100)
  --top <n>                Show only the top N entries (thresholds check all)
  --config <path>          Load config from a specific file
  --help, -h               Show this help message
  --version, -v            Show version number

Subcommands:
  skill               Manage the bundled AI skill (install | uninstall | show | path)"""


def main():
    if _handle_skill_command():
        return

    try:
        opts = parse_options(sys.argv[1:])
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)

    if opts.mode == "help":
        print(_format_help())
        return

    if opts.mode == "version":
        try:
            v = pkg_version("crap4py")
        except Exception:
            v = "0.1.0"
        print(v)
        return

    config = load_config(opts.config_path)
    merged = merge_config_into_options(opts, config)
    code = run_report(merged)
    if code != 0:
        sys.exit(code)


if __name__ == "__main__":
    main()
