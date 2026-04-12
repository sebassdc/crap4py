---
name: crap4py
description: Use when the user asks for a CRAP report, cyclomatic complexity analysis, or code quality metrics on a Python project
---

# crap4py — CRAP Metric for Python

Computes the **CRAP** (Change Risk Anti-Pattern) score for every function and method in a Python project. CRAP combines cyclomatic complexity with test coverage to identify functions that are both complex and under-tested.

## Setup

The target project must use `pytest` (default) or `unittest`. Add to its `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.json]
output = "coverage.json"
```

Install crap4py as a uv tool:

```bash
uv tool install crap4py
```

Or as a dev dependency:

```toml
[project.optional-dependencies]
dev = ["crap4py"]
```

## Usage

Run from the project root (where `src/` and `tests/` live):

```bash
# Analyze all source files under src/
crap4py

# Filter to specific modules
crap4py complexity coverage_parser

# Custom source directory
crap4py --src lib

# Exclude paths
crap4py --exclude dist --exclude fixtures

# JSON output for CI pipelines
crap4py --output json

# Markdown table for PR comments
crap4py --output markdown

# CSV for spreadsheets
crap4py --output csv

# CI threshold controls (exit 1 on violation)
crap4py --fail-on-crap 30 --fail-on-coverage-below 70

# Show only top N worst functions
crap4py --top 10

# Custom test runner
crap4py --runner unittest
crap4py --coverage-command "make test-cov"
```

crap4py automatically deletes stale coverage data, runs `coverage run -m pytest`, generates `coverage.json`, and prints the report.

## CLI Options

```
--src <dir>              Source directory (default: src)
--exclude <pattern>      Exclude paths containing pattern (repeatable)
--timeout <seconds>      Timeout in seconds (default: 300)
--output <format>        Output: text, json, markdown, csv (default: text)
--json                   Shorthand for --output json
--runner <pytest|unittest>  Test runner override
--coverage-command <cmd> Custom shell command for coverage
--fail-on-crap <n>       Exit 1 if any CRAP >= n
--fail-on-complexity <n> Exit 1 if any complexity >= n
--fail-on-coverage-below <n>  Exit 1 if any coverage < n (0-100)
--top <n>                Show only top N entries (thresholds check all)
--config <path>          Config file path
--help, -h               Show help
--version, -v            Show version
```

## Configuration File

Create `crap4py.config.json` or `.crap4pyrc.json` in the project root:

```json
{
  "src": "lib",
  "exclude": ["dist", "fixtures"],
  "output": "json",
  "failOnCrap": 30,
  "failOnCoverageBelow": 70,
  "timeout": 120
}
```

CLI flags override config values.

## Output Formats

**Text** (default): fixed-width table
**JSON**: `{"tool": "crap4py", "entries": [...]}`
**Markdown**: GFM table for PR comments
**CSV**: header + rows, comma-quoted fields

## Exit Codes

| Code | Meaning |
|------|---------|
| 0    | Pass |
| 1    | Threshold violation or runtime error |
| 2    | Usage error (invalid flags) |

## Programmatic API

```python
from crap4py import generate_report, crap_score, extract_functions

# Analyze against existing coverage data (does NOT run tests)
result = generate_report(src_dir="src", coverage_path="coverage.json")
for e in result["entries"]:
    print(f"{e['name']}: CRAP {e['crap']}")
```

## Interpreting Scores

| CRAP Score | Meaning |
|-----------|---------|
| 1-5       | Clean — low complexity, well tested |
| 5-30      | Moderate — consider refactoring or adding tests |
| 30+       | Crappy — high complexity with poor coverage |

## How It Works

1. Deletes `.coverage` and `coverage.json` if present
2. Runs `python -m coverage run -m pytest` (or custom command)
3. Runs `python -m coverage json`
4. Finds all `.py` files under the source directory
5. Applies `--exclude` filters
6. Extracts top-level functions and class methods (as `ClassName.method_name`)
7. Computes cyclomatic complexity via Python AST:
   - `if`/`elif`, ternary: +1 each
   - `for`, `while`, `async for`: +1 each
   - `except` handler: +1 each
   - `and`/`or`: +number of operators (len(values) - 1)
   - Comprehension `if` conditions: +1 each
   - `match`/`case` (Python 3.10+): +1 per case
   - Nested functions and classes are skipped
8. Reads `coverage.json` for per-line executed/missing data
9. Applies CRAP formula: `CC² x (1 - cov)³ + CC`
10. Evaluates thresholds, formats output, and prints report
