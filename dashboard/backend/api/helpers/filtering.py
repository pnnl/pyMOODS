"""Shared request-parsing helpers used by multiple routes."""
import pandas as pd


def apply_filters(df: pd.DataFrame, hyperparameters: dict, request_args) -> pd.DataFrame:
    """Filter *df* by any query-string keys that match a hyperparameter name."""
    result = df.copy()
    for key in hyperparameters:
        values = request_args.getlist(key)
        if values:
            result = result[result[key].isin(values)]
    return result


def apply_column_filters(df: pd.DataFrame, skip_keys: set, request_args) -> pd.DataFrame:
    """Filter *df* by any request arg that maps to a DataFrame column, skipping *skip_keys*."""
    result = df.copy()
    for key in request_args:
        if key in skip_keys:
            continue
        values = request_args.getlist(key)
        if values and key in result.columns:
            result = result[result[key].isin(values)]
    return result


def parse_weights(request_args, objective_keys: list, default: float = 1.0) -> dict:
    """Parse ``weight_<obj>`` query params into a dict, filling missing keys with *default*."""
    weights: dict = {}
    for key in request_args:
        if key.startswith("weight_"):
            obj_name = key[len("weight_"):]
            try:
                weights[obj_name] = float(request_args[key])
            except ValueError:
                weights[obj_name] = default
    for obj in objective_keys:
        weights.setdefault(obj, default)
    return weights
