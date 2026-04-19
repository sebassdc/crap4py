# crap4py

**CRAP** (Change Risk Anti-Pattern) metric for Python projects.

Combines cyclomatic complexity with test coverage to identify functions that are both complex and under-tested -- the riskiest code to change.

## Quick Start

Install the CLI from this checkout:

```bash
uv tool install .
```

For local development in this repository:

```bash
uv sync
```

Or, if you're using it in another project, add to your `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = ["crap4py", "pytest>=7", "coverage[toml]>=7"]
```

Configure coverage.py to emit JSON output in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.json]
output = "coverage.json"
```

Run from your project root (where `src/` lives):

```bash
crap4py
```

Or invoke as a module:

```bash
python -m crap4py
```

crap4py automatically deletes stale coverage data, runs your test suite with coverage, and prints the report.

## Output

```
CRAP Report
===========
Function                       Module                              CC   Cov%     CRAP
-------------------------------------------------------------------------------------
complex_fn                     my.module                          12   45.0%    130.2
simple_fn                      my.module                           1  100.0%      1.0
```

## CLI Options

```bash
crap4py --help                  # show usage and available options
crap4py --version               # print version number
crap4py --src lib               # analyze from lib/ instead of src/
crap4py --exclude dist          # exclude paths containing "dist"
crap4py --timeout 120           # set analysis timeout to 120 seconds
```

## Configuration File

Instead of passing flags every time, create a `crap4py.config.json` (or `.crap4pyrc.json`) in your project root:

```json
{
  "src": "lib",
  "exclude": ["dist", "fixtures"],
  "output": "json",
  "failOnCrap": 30,
  "timeout": 120
}
```

### File Discovery

crap4py looks for config files in the current working directory in this order:

1. `crap4py.config.json` (preferred)
2. `.crap4pyrc.json` (fallback)

The first file found is used. If neither exists, all options use their defaults.

To load a config file from a custom path, use the `--config` flag:

```bash
crap4py --config configs/crap4py.json
```

### CLI Override Precedence

CLI flags always take precedence over config file values. For example, if your config file sets `"src": "lib"` but you run `crap4py --src app`, the `app` directory is used.

### Supported Keys

| Key                  | Type       | Description                                      | Default |
|----------------------|------------|--------------------------------------------------|---------|
| `src`                | `string`   | Source directory to analyze                       | `"src"` |
| `exclude`            | `string[]` | Exclude paths containing these patterns           | `[]`    |
| `output`             | `string`   | Output format: `"text"`, `"json"`, `"markdown"`, or `"csv"` | `"text"`|
| `runner`             | `string`   | Test runner: `"pytest"` or `"unittest"`          | auto    |
| `coverageCommand`    | `string`   | Custom shell command to generate coverage         | none    |
| `failOnCrap`         | `number`   | Fail if any CRAP score >= this value             | none    |
| `failOnComplexity`   | `number`   | Fail if any cyclomatic complexity >= this value  | none    |
| `failOnCoverageBelow`| `number`   | Fail if any function coverage < this % (0-100)   | none    |
| `top`                | `number`   | Show only the top N entries                       | all     |
| `timeout`            | `number`   | Analysis timeout in seconds                       | `300`   |

Unknown keys are silently ignored, so config files are forward-compatible with future versions.

## Programmatic API

crap4py can be used as a library in your own tools and scripts. The API assumes coverage data already exists (run your test suite with coverage first).

```python
from crap4py import generate_report, crap_score, extract_functions

# High-level: analyze an entire source tree against existing coverage
result = generate_report(
    src_dir="src",
    coverage_path="coverage.json",
)

for e in result["entries"]:
    print(f"{e['name']}: CRAP {e['crap']}")
```

### `generate_report(src_dir, coverage_path, filters, excludes)`

Finds source files, parses coverage, analyzes each file, and returns entries sorted by CRAP score. This does **not** run your test suite -- it reads from an existing `coverage.json`.

| Option          | Type       | Description                                       | Default          |
|-----------------|------------|---------------------------------------------------|------------------|
| `src_dir`       | `str`      | Source directory to scan for `.py` files           | `"src"`          |
| `coverage_path` | `str`      | Path to `coverage.json` file                      | `"coverage.json"`|
| `filters`       | `list[str]`| Only include files matching these substrings       | `[]`             |
| `excludes`      | `list[str]`| Exclude files whose path contains these substrings | `[]`             |

### Low-level exports

For fine-grained control, individual functions are also exported:

```python
from crap4py import (
    extract_functions,      # parse a Python source string into FunctionInfo list
    parse_coverage,         # read coverage.json from a file path
    coverage_for_range,     # get coverage % for a line range
    source_to_module,       # convert file path to dotted module name
    normalize_path,         # normalize a file path for coverage lookup
    crap_score,             # compute CRAP score from complexity and coverage
    sort_by_crap,           # sort CrapEntry list by CRAP descending
    format_report,          # render text table from CrapEntry list
    format_json_report,     # render JSON string from CrapEntry list
    format_markdown_report, # render markdown table from CrapEntry list
    format_csv_report,      # render CSV string from CrapEntry list
    find_source_files,      # find all .py files in a directory
    filter_sources,         # filter file list by substring patterns
    CrapEntry,              # dataclass for a single report entry
    FunctionInfo,           # dataclass for an extracted function
)
```

## CI Integration

Use threshold flags to fail CI when code quality drops below acceptable levels:

```bash
# Fail if any function has CRAP >= 30 or coverage below 70%
crap4py --fail-on-crap 30 --fail-on-coverage-below 70

# Fail if any function has complexity >= 15, show only top 10
crap4py --fail-on-complexity 15 --top 10
```

Multiple thresholds can be combined. The report is always printed before any failure.

The `--top` flag limits displayed entries but all entries are evaluated against thresholds.

### Exit Codes

| Code | Meaning |
|------|---------|
| 0    | Pass -- no threshold violations |
| 1    | Threshold violated or runtime error |
| 2    | Usage error (invalid flags or arguments) |

## Output Formats

crap4py supports four output formats:

```bash
crap4py                          # default text table
crap4py --json                   # JSON (shorthand for --output json)
crap4py --output markdown        # Markdown table
crap4py --output csv             # CSV
```

### Text (default)

```
CRAP Report
===========
Function                       Module                              CC   Cov%     CRAP
-------------------------------------------------------------------------------------
complex_fn                     my.module                          12   45.0%    130.2
simple_fn                      my.module                           1  100.0%      1.0
```

### JSON

```json
{
  "tool": "crap4py",
  "entries": [
    {
      "name": "complex_fn",
      "module": "my.module",
      "complexity": 12,
      "coverage": 45,
      "crap": 130.2
    }
  ]
}
```

### Markdown

```markdown
# CRAP Report

| Function | Module | CC | Cov% | CRAP |
|---|---|---:|---:|---:|
| complex_fn | my.module | 12 | 45.0% | 130.2 |
| simple_fn | my.module | 1 | 100.0% | 1.0 |
```

### CSV

```csv
Function,Module,CC,Coverage,CRAP
complex_fn,my.module,12,45.0,130.2
simple_fn,my.module,1,100.0,1.0
```

Text output is the default. Use `--json` as a shorthand or `--output <format>` for any format.

## Excluding Paths

Use `--exclude` to filter out files whose path contains a given substring. The flag is repeatable:

```bash
# Skip dist and fixtures directories
crap4py --exclude dist --exclude fixtures

# Analyze lib/ but skip generated code
crap4py --src lib --exclude __generated__

# Combine with other options
crap4py --src packages/core/src --exclude __mocks__ --exclude test_fixtures --json
```

## Filtering

Pass module path fragments as arguments to filter:

```bash
crap4py parser validator   # only files matching those strings
```

## CRAP Formula

```
CRAP(fn) = CC^2 * (1 - coverage)^3 + CC
```

- **CC** = cyclomatic complexity (decision points + 1)
- **coverage** = fraction of lines covered by tests

| Score | Risk |
|-------|------|
| 1-5   | Low -- clean code |
| 5-30  | Moderate -- refactor or add tests |
| 30+   | High -- complex and under-tested |

## What It Counts

Decision points that increase cyclomatic complexity:

- `if` / `elif` / ternary (`x if c else y`)
- `for` / `while` / `async for`
- `except` handlers (each one counts)
- `and` / `or` (each operator counts)
- Comprehension `if` conditions
- `match`/`case` clauses (Python 3.10+)

Nested functions and classes are skipped -- only the enclosing function's body is analyzed.

## Compatibility

| Layout | Status | Notes |
|--------|--------|-------|
| Standard (`src/`) | Supported | Default, no config needed |
| Custom source dir | Supported | Use `--src <dir>` |
| Monorepo workspace | Supported | Point `--src` to package source |
| Multiple src dirs | Supported | Use `--exclude` to filter |
| POSIX paths | Supported | Normalized internally |
| coverage.py JSON format | Required | Other formats not supported |
| Branch coverage | Not used | Statement/line coverage only |

## Limitations

- Only Python (`.py`) files are analyzed -- other file types are ignored.
- Only functions found within the configured source directory (default: `src/`) are scanned.
- Coverage data must be in coverage.py JSON format (`coverage.json`). Other coverage formats are not supported.
- Runner detection is heuristic: crap4py checks for pytest first, then falls back to unittest. Use `--runner pytest|unittest` to override.
- Nested functions are attributed to their enclosing function rather than being extracted as separate symbols.
- Dynamic or computed method names are not extracted.
- Only line coverage is used when computing the coverage fraction -- branch and function coverage are ignored.
- Coverage is calculated using line-to-function overlap: a line is attributed to a function if it falls within the function's line range. This is an approximation; edge cases at function boundaries may occur.

For advanced usage patterns, see [docs/advanced-usage.md](docs/advanced-usage.md).

## Runner Configuration

crap4py supports three ways to run your test suite for coverage, applied in this order of precedence:

### 1. `--coverage-command` (highest priority)

Run an arbitrary shell command instead of the built-in runner logic. The command is executed with `shell=True`, so pipes, environment variables, and shell syntax all work.

```bash
# Monorepo: run tests only for a specific package
crap4py --coverage-command "coverage run -m pytest packages/core/tests"

# Custom script with environment variables
crap4py --coverage-command "CI=1 coverage run -m pytest --cov-report=json"

# Tox or nox
crap4py --coverage-command "tox -e coverage"
```

The command must produce a `coverage.json` file in coverage.py JSON format.

### 2. `--runner pytest|unittest` (skip auto-detection)

Use the built-in runner invocation for pytest or unittest, but skip the heuristic:

```bash
# Force unittest even if pytest is installed
crap4py --runner unittest

# Force pytest explicitly
crap4py --runner pytest
```

### 3. Auto-detection (default)

When neither flag is provided, crap4py detects the runner automatically:

1. If pytest is available, use pytest.
2. Otherwise, fall back to unittest.

## Troubleshooting

| Error | Fix |
|-------|-----|
| `Source directory 'src' not found` | Use `--src <dir>` to point to your source directory |
| `No Python files found` | Verify your source directory contains `.py` files |
| `No files match the filters` | Check your filter arguments match actual file paths |
| `Coverage run failed` | Ensure your test suite passes independently before running crap4py |
| `No coverage.json found` | Configure coverage.py to output JSON format (see Quick Start) |
| `Coverage run timed out` | Increase timeout with `--timeout <seconds>` |
| `Config file not found` | Check the path passed to `--config` exists |
| `Invalid JSON in config` | Fix the JSON syntax in your config file |

## Agent Skill

crap4py ships a bundled `SKILL.md` that you can install into the cross-agent
skill directory consumed by Claude Code, Codex, Pi, and any harness that reads
`.agents/skills/`.

```bash
# Global install for the current user (~/.agents/skills/crap4py/SKILL.md)
crap4py skill install

# Project-local install (./.agents/skills/crap4py/SKILL.md)
crap4py skill install --project

# Print the bundled skill
crap4py skill show

# Print where the skill is (or would be) installed
crap4py skill path
crap4py skill path --project

# Remove
crap4py skill uninstall
crap4py skill uninstall --project
```

The bundled skill lives inside the published package at `src/crap4py/skill/SKILL.md`.

### Claude Code Symlink

Claude Code discovers skills from its local plugin directory, not from
`~/.agents/skills/`. After installing, create a symlink so Claude Code picks up
the skill automatically:

```bash
# Install the skill to the cross-agent directory first
crap4py skill install

# Symlink into the Claude Code plugin directory
mkdir -p ~/.claude/plugins/local/plugins/crap4py/skills/crap4py
ln -sf ~/.agents/skills/crap4py/SKILL.md \
       ~/.claude/plugins/local/plugins/crap4py/skills/crap4py/SKILL.md
```

To verify it worked:

```bash
ls -l ~/.claude/plugins/local/plugins/crap4py/skills/crap4py/SKILL.md
```

You should see a symlink pointing to the installed skill file.

## Development

```bash
uv sync
uv run pytest tests/        # run tests
uv run python -m crap4py    # run on own source
```

## Inspiration

Inspired by [crap4clj](https://github.com/unclebob/crap4clj) by Robert C. Martin (Uncle Bob).

## License

MIT. See [LICENSE](LICENSE).
