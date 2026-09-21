"""Objective ranking utilities built on TradeoffLattice."""
import numpy as np
import pandas as pd
from tradeoff_lattice import TradeoffLattice


def _ascending_objectives(objective_functions: dict) -> list:
    return [
        k for k, v in objective_functions.items()
        if isinstance(v, dict) and v.get('direction') == 'maximize'
    ]


def create_lattice(
    df: pd.DataFrame,
    objective_functions: dict,
    decision_variables: dict,
) -> TradeoffLattice:
    return TradeoffLattice(
        df=df,
        ovars=list(objective_functions.keys()),
        dvars=list(decision_variables.keys()),
        ascending=_ascending_objectives(objective_functions),
    )


def get_objective_rank_frame(
    df: pd.DataFrame,
    objective_functions: dict,
    decision_variables: dict,
) -> pd.DataFrame:
    lattice = create_lattice(df, objective_functions, decision_variables)
    objective_keys = list(objective_functions.keys())
    raw = lattice.rank[objective_keys].astype(float)

    def _to_1_10(col: pd.Series) -> pd.Series:
        lo, hi = col.min(), col.max()
        if pd.isna(lo) or pd.isna(hi) or lo == hi:
            return pd.Series(1, index=col.index, dtype=int)
        return (1 + (col - lo) * 9.0 / (hi - lo)).round().clip(1, 10).astype(int)

    return raw.apply(_to_1_10, axis=0)


def build_rank_dict(rank_frame: pd.DataFrame, row_data=None, key_builder=None) -> dict:
    ranks: dict = {}
    for idx, row in rank_frame.iterrows():
        key = key_builder(row_data.loc[idx], idx) if (key_builder and row_data is not None) else str(idx)
        ranks[key] = row.to_dict()
    return ranks


def build_filtered_solution_ranks(
    filtered_data: pd.DataFrame,
    objective_functions: dict,
    decision_variables: dict,
    selected_rows: pd.DataFrame,
    key_builder=None,
) -> dict:
    rank_frame = get_objective_rank_frame(filtered_data, objective_functions, decision_variables)
    selected = rank_frame.loc[selected_rows.index]
    return build_rank_dict(selected, row_data=selected_rows, key_builder=key_builder)


def build_solution_rank_key(row, fallback_index) -> str:
    parts = []
    if 'Solution ID' in row:
        parts.append(str(row['Solution ID']))
    for col in row.index:
        if 'config' in col.lower() or 'scenario' in col.lower():
            parts.append(str(row[col]))
    return ','.join(parts) if parts else str(fallback_index)


# Kept as an alias — some callers (lattice.py) use this name
build_solution_lattice_key = build_solution_rank_key


def compute_topsis(
    df: pd.DataFrame,
    ovars: list,
    obj_directions: dict,
    weights: dict,
) -> pd.Series:
    """TOPSIS: returns closeness coefficient per solution (higher = better)."""
    matrix = df[ovars].astype(float).values  # (n_solutions, n_objectives)

    # Normalize columns (Euclidean norm)
    norms = np.sqrt((matrix ** 2).sum(axis=0))
    norms[norms == 0] = 1.0
    normalized = matrix / norms

    # Apply weights
    w = np.array([weights.get(obj, 1.0 / len(ovars)) for obj in ovars])
    weighted = normalized * w

    # Ideal best / worst per objective direction
    ideal_best = np.array([
        weighted[:, j].max() if obj_directions.get(obj) == 'maximize'
        else weighted[:, j].min()
        for j, obj in enumerate(ovars)
    ])
    ideal_worst = np.array([
        weighted[:, j].min() if obj_directions.get(obj) == 'maximize'
        else weighted[:, j].max()
        for j, obj in enumerate(ovars)
    ])

    d_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    d_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    cc = d_worst / (d_best + d_worst + 1e-10)
    return pd.Series(cc, index=df.index)


def compute_vikor(
    df: pd.DataFrame,
    ovars: list,
    obj_directions: dict,
    weights: dict,
    v: float = 0.5,
) -> pd.Series:
    """VIKOR: returns compromise Q score per solution (lower = better)."""
    matrix = df[ovars].astype(float).values
    w = np.array([weights.get(obj, 1.0 / len(ovars)) for obj in ovars])

    f_best = np.array([
        matrix[:, j].max() if obj_directions.get(obj) == 'maximize'
        else matrix[:, j].min()
        for j, obj in enumerate(ovars)
    ])
    f_worst = np.array([
        matrix[:, j].min() if obj_directions.get(obj) == 'maximize'
        else matrix[:, j].max()
        for j, obj in enumerate(ovars)
    ])

    diffs = np.abs(f_best - f_worst)
    diffs[diffs == 0] = 1.0  # avoid zero-division when all solutions are equal

    weighted_dist = w * np.abs(f_best - matrix) / diffs  # (n_solutions, n_objectives)

    S = weighted_dist.sum(axis=1)   # utility measure
    R = weighted_dist.max(axis=1)   # regret measure

    S_star, S_minus = S.min(), S.max()
    R_star, R_minus = R.min(), R.max()

    Q = (
        v * (S - S_star) / (S_minus - S_star + 1e-10)
        + (1 - v) * (R - R_star) / (R_minus - R_star + 1e-10)
    )
    return pd.Series(Q, index=df.index)
