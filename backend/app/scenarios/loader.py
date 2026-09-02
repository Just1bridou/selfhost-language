import os
from pathlib import Path

import yaml
from pydantic import ValidationError

from app.scenarios.schema import Scenario


class ScenarioLoadError(Exception):
    """Raised when a scenario file fails to load or validate."""


_APP_DIR = Path(__file__).resolve().parent.parent.parent
_DEFAULT_SCENARIOS_DIR = _APP_DIR / "scenarios"

_scenarios: dict[str, Scenario] = {}


def load_scenarios(directory: str | Path | None = None) -> list[Scenario]:
    """Scan `directory` (default: $SCENARIOS_DIR or ./scenarios) for *.yaml
    files, validate each against the Scenario schema, and replace the
    module-level scenario cache with the result. A missing or empty
    directory yields an empty list rather than raising."""
    global _scenarios

    if directory is None:
        directory = os.environ.get("SCENARIOS_DIR", str(_DEFAULT_SCENARIOS_DIR))
    directory = Path(directory)

    scenarios: dict[str, Scenario] = {}

    if directory.is_dir():
        for path in sorted(directory.glob("*.yaml")):
            try:
                raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                scenario = Scenario.model_validate(raw)
            except (yaml.YAMLError, ValidationError) as exc:
                raise ScenarioLoadError(f"invalid scenario file {path}: {exc}") from exc
            scenarios[scenario.id] = scenario

    _scenarios = scenarios
    return list(_scenarios.values())


def get_scenario(scenario_id: str) -> Scenario | None:
    return _scenarios.get(scenario_id)


def list_scenarios() -> list[Scenario]:
    return list(_scenarios.values())


# Load eagerly at import time so scenarios are ready "at startup" (AC#2/#3) as
# soon as anything imports this module, without requiring a change to
# app/main.py (owned by story 1.2). Safe to call with no scenarios present yet
# (AC#5) — 3.2 populates the default directory with real content.
load_scenarios()
