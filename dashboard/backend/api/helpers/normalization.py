"""Value normalisation and solution display helpers."""
from collections import OrderedDict

import numpy as np
import pandas as pd

# Columns always excluded from JSON display payloads
_DISPLAY_EXCLUDE = frozenset({'File Name', 'x_coord', 'y_coord', 'label'})

# Preferred column ordering for solution tables (use-case specific; extras appended)
_DESIRED_COLUMN_ORDER = [
    'Solution ID', 'Location Scenario', 'Operation Model', 'Parameter Set',
    'Reliability Weight', 'Cost Weight', 'Reliability Index', 'N Contingencies',
    'Expansion Budget Cap', 'Minimum Reliability Index', 'Voltage Deviation Limit',
    'Design Id', 'Expansion Cost', 'Expected Datacenter Load Shed',
    'Expected Total Load Shed', 'Weighted Sum',
]


def to_python_scalar(value):
    if isinstance(value, np.generic):
        return value.item()
    return value


def normalize_value(value):
    """Return None for NaN, plain Python scalar for numpy types."""
    if isinstance(value, float) and np.isnan(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, np.generic):
        return value.item()
    return value


def normalize_rank_dict(rank_dict: dict) -> dict:
    return {str(k): to_python_scalar(v) for k, v in rank_dict.items()}


def order_solutions_for_display(
    df: pd.DataFrame,
    desired_order: list | None = None,
    exclude: set | None = None,
) -> list:
    """Convert a DataFrame to a list of OrderedDicts with a preferred column order."""
    if desired_order is None:
        desired_order = _DESIRED_COLUMN_ORDER
    if exclude is None:
        exclude = _DISPLAY_EXCLUDE

    result = []
    for _, row in df.iterrows():
        ordered = OrderedDict()
        for col in desired_order:
            if col in row.index and col not in exclude:
                ordered[col] = row[col]
        for col in row.index:
            if col not in ordered and col not in exclude:
                ordered[col] = row[col]
        result.append(ordered)
    return result
