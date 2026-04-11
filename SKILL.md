---
name: crap4py
description: Use when the user asks for a CRAP report, cyclomatic complexity analysis, or code quality metrics on a Python project
---

# crap4py — CRAP Metric for Python

Computes the **CRAP** (Change Risk Anti-Pattern) score for every function and method in a Python project. CRAP combines cyclomatic complexity with test coverage to identify functions that are both complex and under-tested.

## Setup

The target project must use `pytest`. Add to its `pyproject.toml`:

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
```

crap4py automatically deletes stale coverage data, runs `coverage run -m pytest`, generates `coverage.json`, and prints the report.

### Output

A table sorted by CRAP score (worst first):

```
CRAP Report
===========
Function                       Module                              CC   Cov%     CRAP
-------------------------------------------------------------------------------------
complex_fn                     my.module                          12   45.0%    130.2
simple_fn                      my.module                           1  100.0%      1.0
```

## Interpreting Scores

| CRAP Score | Meaning |
|-----------|---------|
| 1-5       | Clean — low complexity, well tested |
| 5-30      | Moderate — consider refactoring or adding tests |
| 30+       | Crappy — high complexity with poor coverage |

## How It Works

1. Deletes `.coverage` and `coverage.json` if present
2. Runs `python -m coverage run -m pytest`
3. Runs `python -m coverage json`
4. Finds all `.py` files under `src/`
5. Extracts top-level functions and class methods (as `ClassName.method_name`)
6. Computes cyclomatic complexity via Python AST:
   - `if`/`elif`, ternary: +1 each
   - `for`, `while`, `async for`: +1 each
   - `except` handler: +1 each
   - `and`/`or`: +number of operators (len(values) - 1)
   - Comprehension `if` conditions: +1 each
   - `match`/`case` (Python 3.10+): +1 per case
   - Nested functions and classes are skipped
7. Reads `coverage.json` for per-line executed/missing data
8. Applies CRAP formula: `CC² × (1 - cov)³ + CC`
9. Sorts by CRAP score descending and prints report
