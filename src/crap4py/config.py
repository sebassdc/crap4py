"""Config file loading and merging for crap4py."""

import json
import os
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, Optional

from crap4py.options import CliOptions

_DISCOVERY_FILES = ["crap4py.config.json", ".crap4pyrc.json"]


def load_config(explicit_path: Optional[str] = None) -> Dict[str, Any]:
    """Load a JSON config file.

    If *explicit_path* is given the file must exist; otherwise we look for
    ``crap4py.config.json`` then ``.crap4pyrc.json`` in the current working
    directory.  Returns an empty dict when no config file is found during
    auto-discovery.
    """
    if explicit_path is not None:
        p = Path(explicit_path)
        if not p.is_file():
            raise ValueError(f"Config file not found: {explicit_path}")
        return _parse_file(p)

    for name in _DISCOVERY_FILES:
        candidate = Path.cwd() / name
        if candidate.is_file():
            return _parse_file(candidate)

    return {}


def _parse_file(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(
            f"Config file {path} must contain a JSON object, got {type(data).__name__}"
        )
    return data


def merge_config_into_options(opts: CliOptions, config: Dict[str, Any]) -> CliOptions:
    """Return a new CliOptions with config values applied where CLI kept defaults.

    CLI flags always take precedence.  Config keys use camelCase mapping:

    - ``src`` -> src_dir (only if CLI is default ``"src"``)
    - ``exclude`` -> excludes (only if CLI is empty)
    - ``output`` -> output (only if CLI is default ``"text"``)
    - ``timeout`` -> timeout_s (only if CLI is default ``300``)
    - ``runner`` -> runner (only if CLI is ``None``)
    - ``coverageCommand`` -> coverage_command (only if CLI is ``None``)
    - ``failOnCrap`` -> fail_on_crap (only if CLI is ``None``)
    - ``failOnComplexity`` -> fail_on_complexity (only if CLI is ``None``)
    - ``failOnCoverageBelow`` -> fail_on_coverage_below (only if CLI is ``None``)
    - ``top`` -> top (only if CLI is ``None``)
    """
    kwargs: Dict[str, Any] = {}

    # Fields with non-None defaults — config used only when CLI kept the default
    if opts.src_dir == "src" and "src" in config:
        kwargs["src_dir"] = config["src"]

    if not opts.excludes and "exclude" in config:
        kwargs["excludes"] = config["exclude"]

    if opts.output == "text" and "output" in config:
        kwargs["output"] = config["output"]

    if opts.timeout_s == 300 and "timeout" in config:
        kwargs["timeout_s"] = config["timeout"]

    # Optional fields — config used only when CLI is None
    _optional_map = {
        "runner": "runner",
        "coverageCommand": "coverage_command",
        "failOnCrap": "fail_on_crap",
        "failOnComplexity": "fail_on_complexity",
        "failOnCoverageBelow": "fail_on_coverage_below",
        "top": "top",
    }

    for config_key, field_name in _optional_map.items():
        if getattr(opts, field_name) is None and config_key in config:
            kwargs[field_name] = config[config_key]

    return replace(opts, **kwargs)
