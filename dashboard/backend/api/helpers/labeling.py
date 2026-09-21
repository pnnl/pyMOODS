"""Scenario labeling and representative-selection helpers."""
import pandas as pd

from helpers.normalization import normalize_value


def ensure_unique_labels(labels: list) -> list:
    counts: dict = {}
    result = []
    for label in labels:
        n = counts.get(label, 0)
        counts[label] = n + 1
        result.append(label if n == 0 else f"{label} #{n + 1}")
    return result


def get_scenario_dimension_keys(data: dict, csv_data: pd.DataFrame) -> list:
    """Return keys that define distinct scenarios, preferring explicitly enumerated values."""
    explicit, fallback = [], []
    for section in (data.get("input_parameters", {}), data.get("hyperparameters", {})):
        for key, meta in section.items():
            if key not in csv_data.columns:
                continue
            if isinstance(meta, dict) and isinstance(meta.get("values"), list):
                explicit.append(key)
            elif not pd.api.types.is_numeric_dtype(csv_data[key]):
                fallback.append(key)
    return explicit or fallback


def get_filter_dimension_keys(data: dict, csv_data: pd.DataFrame) -> list:
    candidates = (
        list(data.get("input_parameters", {}).keys()) +
        list(data.get("hyperparameters", {}).keys())
    )
    return [k for k in candidates if k in csv_data.columns]


def build_scenario_label(row, scenario_keys: list) -> str:
    if not scenario_keys:
        return str(row.name)
    return "<br>".join(f"{k}: {normalize_value(row.get(k))}" for k in scenario_keys)


def build_flat_label(row, scenario_keys: list) -> str:
    if not scenario_keys:
        return str(row.name)
    return " | ".join(str(normalize_value(row.get(k))) for k in scenario_keys)


def pick_scenario_representatives(
    df: pd.DataFrame,
    scenario_keys: list,
    objective_keys: list,
    objective_functions: dict,
    weights: dict,
) -> pd.DataFrame:
    if not scenario_keys:
        return df.copy()

    frame = df.copy()
    score = pd.Series(0.0, index=frame.index)

    for key in objective_keys:
        series = pd.to_numeric(frame[key], errors='coerce')
        if series.isna().all():
            continue
        lo, hi = series.min(), series.max()
        normed = (
            pd.Series(1.0, index=series.index)
            if (pd.isna(lo) or lo == hi)
            else (series - lo) / (hi - lo)
        )
        direction = objective_functions.get(key, {}).get("direction")
        beneficial = normed if direction == "maximize" else (1 - normed)
        score += beneficial.fillna(0) * float(weights.get(key, 1.0))

    frame["_score"] = score
    best = frame.groupby(scenario_keys)["_score"].idxmax()
    return (
        frame.loc[best]
        .drop(columns=["_score"])
        .sort_values(scenario_keys)
        .reset_index(drop=True)
    )
