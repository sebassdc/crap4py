# Advanced Usage

This document covers advanced invocation patterns, CI integration, and troubleshooting for crap4py.

## Monorepo Invocation

In a monorepo, point crap4py at a specific package's source directory:

```bash
crap4py --src packages/core/src
```

crap4py will look for `coverage.json` and run tests scoped to that directory. Run this from the package root that contains the relevant `pyproject.toml` and test config.

For monorepos using a custom coverage command:

```bash
crap4py --src packages/api/src --coverage-command "coverage run -m pytest packages/api/tests"
```

## Custom Source Roots

If your Python source lives outside `src/`, specify it explicitly:

```bash
crap4py --src lib
```

Any directory name is accepted. The path is resolved relative to the current working directory.

You can also combine custom source roots with exclusions:

```bash
crap4py --src app --exclude migrations --exclude __pycache__
```

## JSON Output in CI

Emit machine-readable JSON for downstream processing, threshold checks, or artifact storage:

```bash
crap4py --json > report.json
```

The output schema:

```json
{
  "tool": "crap4py",
  "entries": [
    {
      "name": "my_function",
      "module": "my.module",
      "complexity": 5,
      "coverage": 80,
      "crap": 5.2
    }
  ]
}
```

In a CI step you can fail the build when high-CRAP entries are present:

```bash
crap4py --json > report.json
python -c "
import json, sys
r = json.load(open('report.json'))
hot = [e for e in r['entries'] if e['crap'] > 30]
if hot:
    print('High CRAP:', [e['name'] for e in hot], file=sys.stderr)
    sys.exit(1)
"
```

Or use the built-in threshold flags for simpler CI integration:

```bash
# Fail the build if any function has CRAP >= 30
crap4py --fail-on-crap 30

# Combine thresholds and output JSON for artifact storage
crap4py --fail-on-crap 30 --fail-on-coverage-below 60 --json > report.json
```

### GitHub Actions Example

```yaml
- name: CRAP Report
  run: |
    uv sync
    uv run crap4py --fail-on-crap 30 --fail-on-coverage-below 60
```

### GitLab CI Example

```yaml
crap-report:
  script:
    - uv sync
    - uv run crap4py --fail-on-crap 30 --json > crap-report.json
  artifacts:
    paths:
      - crap-report.json
```

## Filtering by Module Path Fragment

Pass one or more path fragments as positional arguments to restrict the report to matching files:

```bash
crap4py auth payment
```

crap4py retains only entries whose module path contains at least one of the supplied fragments. This is useful for focusing on a specific feature area without changing your source directory.

Combine with exclusions for precise control:

```bash
crap4py --exclude test_helpers auth   # auth modules, skip test helpers
```

## Skill Management

crap4py ships a bundled `SKILL.md` for cross-agent harnesses (Claude Code, Codex, Pi, etc.):

```bash
# Install globally (~/.agents/skills/crap4py/SKILL.md)
crap4py skill install

# Install project-locally (./.agents/skills/crap4py/SKILL.md)
crap4py skill install --project

# Print the bundled skill content
crap4py skill show

# Print the resolved install path
crap4py skill path
crap4py skill path --project

# Remove
crap4py skill uninstall
crap4py skill uninstall --project
```

Once installed, ask your AI coding agent for a "CRAP report" and it will know how to run crap4py and interpret the results.

## Timeout Adjustment

The default timeout for the coverage run is 300 seconds. For large test suites, increase it:

```bash
crap4py --timeout 600
```

The value is in seconds. If the coverage run exceeds the timeout, crap4py exits with an error. Increase proportionally to your suite's typical wall-clock time.

You can also set this in a config file to avoid passing it every time:

```json
{
  "timeout": 600
}
```

---

## Troubleshooting

### `Source directory 'src' not found`

Your project uses a different source root. Fix it with:

```bash
crap4py --src <your-source-dir>
```

### `No Python files found`

The source directory exists but contains no `.py` files. Verify the path and check that you are not accidentally pointing at a build output directory (`dist/`, `build/`).

### `No files match the filters`

Your filter arguments do not match any module paths in the report. Module paths are derived from the file path relative to the project root, with `/` replaced by `.`. Run without filters first to see the full list of module names, then narrow down.

### `Coverage run failed`

The test suite itself is failing. Run your tests independently first:

```bash
coverage run -m pytest
# or
python -m pytest
```

Fix any failures, then re-run crap4py.

### `No coverage.json found`

Your test runner is not emitting coverage.py JSON output. Add JSON reporting to your `pyproject.toml`:

```toml
[tool.coverage.json]
output = "coverage.json"
```

Then re-run. Alternatively, generate coverage manually:

```bash
coverage run -m pytest
coverage json
```

### `Coverage run timed out`

The test suite takes longer than the configured timeout. Increase it:

```bash
crap4py --timeout 600
```

If your suite is inherently slow, consider running it separately and pointing crap4py at a pre-existing `coverage.json` via the programmatic API:

```python
from crap4py import generate_report

result = generate_report(src_dir="src", coverage_path="coverage.json")
```

### `Config file not found`

The path passed to `--config` does not exist. Verify the path is correct and the file is accessible:

```bash
ls -la configs/crap4py.json
crap4py --config configs/crap4py.json
```

### `Invalid JSON in config`

Your config file contains malformed JSON. Validate it with:

```bash
python -m json.tool crap4py.config.json
```

Fix any syntax errors and re-run.
