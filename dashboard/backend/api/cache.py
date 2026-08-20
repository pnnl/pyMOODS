"""
In-memory case-study cache.

All routes call ``get_or_load(name)`` rather than accessing the dict directly.
"""
import json
import os

import pandas as pd

from config import DEMO_DATA_DIR

_CACHE: dict = {}


def get_or_load(name: str) -> dict:
    """Return cached data for *name*, loading from disk on first call."""
    if name not in _CACHE:
        _load(name)
    return _CACHE[name]


def _load(name: str) -> None:
    json_path = os.path.join(DEMO_DATA_DIR, f"{name}.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Case study JSON not found: {json_path}")

    with open(json_path) as fh:
        data = json.load(fh)

    csv_file = data.get("datafile")
    if not csv_file:
        raise ValueError(f"'datafile' key missing in {name}.json")

    csv_path = os.path.join(DEMO_DATA_DIR, csv_file)
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    csv_data = pd.read_csv(csv_path)
    csv_data.index.set_names('Solution ID', inplace=True)
    csv_data.index = csv_data.index.astype(int)
    csv_data.reset_index(inplace=True)

    scenario_data = None
    scenario_file = data.get("scenariofile")
    if scenario_file:
        scenario_path = os.path.join(DEMO_DATA_DIR, scenario_file)
        if not os.path.exists(scenario_path):
            raise FileNotFoundError(f"Scenario file not found: {scenario_path}")
        scenario_data = pd.read_csv(scenario_path)

    _CACHE[name] = {
        "hyperparameters":    data.get("hyperparameters", {}),
        "input_parameters":   data.get("input_parameters", {}),
        "objective_functions": data.get("objective_functions", {}),
        "decision_variables": data.get("decision_variables", {}),
        "csv_data":           csv_data,
        "scenario_data":      scenario_data,
    }
