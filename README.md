# crap4py

**CRAP** (Change Risk Anti-Pattern) metric for Python projects.

Combines cyclomatic complexity with test coverage to identify functions that are both complex and under-tested — the riskiest code to change.

## Quick Start

Install as a dev dependency in your project's `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = ["crap4py", "pytest>=7", "coverage[toml]>=7"]
```

Add coverage config:

```toml
[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.json]
output = "coverage.json"
```

Run from the project root:

```bash
uv run python -m crap4py
```

crap4py automatically deletes stale coverage data, runs `coverage run -m pytest`, and prints the report.

## Output

```
CRAP Report
===========
Function                       Module                              CC   Cov%     CRAP
-------------------------------------------------------------------------------------
complex_fn                     my.module                          12   45.0%    130.2
simple_fn                      my.module                           1  100.0%      1.0
```

## Filtering

Pass module path fragments as arguments to filter:

```bash
uv run python -m crap4py complexity coverage   # only files matching those strings
```

## CRAP Formula

```
CRAP(fn) = CC² × (1 - coverage)³ + CC
```

- **CC** = cyclomatic complexity (decision points + 1)
- **coverage** = fraction of lines covered by tests

| Score | Risk |
|-------|------|
| 1-5   | Low — clean code |
| 5-30  | Moderate — refactor or add tests |
| 30+   | High — complex and under-tested |

## What It Counts

Decision points that increase cyclomatic complexity:

- `if` / `elif` / ternary (`x if c else y`)
- `for` / `while` / `async for`
- `except` handlers (each one counts)
- `and` / `or` (each operator counts)
- Comprehension `if` conditions
- `match`/`case` clauses (Python 3.10+)

Nested functions and classes are skipped — only the enclosing function's body is analyzed.

## Agent Skill

crap4py ships with an [Agent Skills](https://agentskills.io) compatible `SKILL.md` that works with Claude Code, Pi, Codex, and any agent that implements the standard.

Install the skill so your AI coding agent can find it:

```bash
# Global — available to all agents, all projects
crap4py skill install

# Project-only — just this repo
crap4py skill install --project
```

This copies the skill to `~/.agents/skills/crap4py/` (global) or `.agents/skills/crap4py/` (project). Once installed, ask your agent for a "CRAP report" and it will know how to run the tool.

Other skill commands:

```bash
crap4py skill show       # Print the SKILL.md to stdout
crap4py skill path       # Show where the skill is installed
crap4py skill uninstall  # Remove the installed skill
```

## Development

```bash
uv sync --extra dev
uv run pytest tests/        # run tests
uv run python -m crap4py    # run on own source
```

## Attribution

This project is inspired by the CRAP metric work and the original `crap4clj` project by Robert C. Martin.

## License

MIT. See [LICENSE](LICENSE).
