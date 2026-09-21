"""
OpenAI-compatible tool schemas and executor for the mooCHAT agentic loop.

Each tool operates on the `context` dict built by routes/chat.py:
    context = {
        "df":                 pd.DataFrame  (already filtered by active filters),
        "objective_keys":     list[str],
        "decision_keys":      list[str],
        "objective_functions": dict,        (includes "unit", "name", etc.)
        "active_weights":     dict[str, float],
    }
"""
import json

import pandas as pd

# ---------------------------------------------------------------------------
# Tool schemas (OpenAI function-calling format)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "query_solutions",
            "description": (
                "Return the top N Pareto-optimal solutions from the current filtered "
                "dataset, ranked by weighted objective score. Use this to answer "
                "questions about specific solution performance, rankings, or values."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "How many top solutions to return (default 5, max 20).",
                    },
                    "sort_by": {
                        "type": "string",
                        "description": (
                            "Objective key to sort by (ascending — lower is better). "
                            "Omit to sort by weighted sum across all objectives."
                        ),
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_variable_statistics",
            "description": (
                "Compute descriptive statistics (min, max, mean, median, std) for "
                "a specific objective or decision variable in the current filtered dataset. "
                "Use this when the user asks about ranges, averages, or spread of a metric."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "variable_name": {
                        "type": "string",
                        "description": (
                            "Exact column name from objectiveKeys or decisionKeys. "
                            "Check available_metadata in the dashboard context first."
                        ),
                    },
                },
                "required": ["variable_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tradeoff_summary",
            "description": (
                "Return a trade-off summary: for each objective, the best achievable "
                "value, worst value, and mean — plus which solution achieves the best. "
                "Use this when the user asks about trade-offs, Pareto fronts, or "
                "which objectives conflict with each other."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_best_compromise",
            "description": (
                "Find the single solution that best balances ALL objectives simultaneously "
                "using normalised weighted scoring. Use this when the user asks for "
                "'the best overall solution', a 'balanced recommendation', or 'what "
                "should I pick'."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_solutions",
            "description": (
                "Compare two solutions side-by-side across all objectives and decision "
                "variables. Use this when the user asks to compare, contrast, or "
                "choose between specific solutions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "solution_id_a": {
                        "type": "integer",
                        "description": "Solution ID (row index) of the first solution.",
                    },
                    "solution_id_b": {
                        "type": "integer",
                        "description": "Solution ID (row index) of the second solution.",
                    },
                },
                "required": ["solution_id_a", "solution_id_b"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Tool executor dispatcher
# ---------------------------------------------------------------------------

def execute_tool(name: str, args: dict, context: dict) -> str:
    """Dispatch a tool call and return a JSON string result."""
    if not context:
        return json.dumps({"error": "No dataset context available — use case not loaded."})
    try:
        dispatch = {
            "query_solutions":       _query_solutions,
            "get_variable_statistics": _get_variable_statistics,
            "get_tradeoff_summary":  _get_tradeoff_summary,
            "find_best_compromise":  _find_best_compromise,
            "compare_solutions":     _compare_solutions,
        }
        fn = dispatch.get(name)
        if fn is None:
            return json.dumps({"error": f"Unknown tool: {name}"})
        return fn(args, context)
    except Exception as exc:
        return json.dumps({"error": f"Tool '{name}' failed: {exc}"})


# ---------------------------------------------------------------------------
# Individual tool implementations
# ---------------------------------------------------------------------------

def _query_solutions(args: dict, context: dict) -> str:
    df: pd.DataFrame      = context["df"]
    obj_keys: list        = context["objective_keys"]
    dec_keys: list        = context["decision_keys"]
    weights: dict         = context["active_weights"]

    top_n    = min(int(args.get("top_n", 5)), 20)
    sort_by  = args.get("sort_by")

    df = df.copy()
    if weights:
        df["_weighted_sum"] = sum(
            pd.to_numeric(df[k], errors="coerce").fillna(0) * weights.get(k, 1.0)
            for k in obj_keys if k in df.columns
        )
        sort_col = sort_by if (sort_by and sort_by in df.columns) else "_weighted_sum"
    else:
        sort_col = sort_by if (sort_by and sort_by in df.columns) else (obj_keys[0] if obj_keys else None)

    if sort_col:
        df_sorted = df.nsmallest(top_n, sort_col)
    else:
        df_sorted = df.head(top_n)

    display_cols = [c for c in ["Solution ID", *obj_keys, *dec_keys] if c in df_sorted.columns]
    records = df_sorted[display_cols].round(4).to_dict(orient="records")
    return json.dumps({
        "solutions":   records,
        "count":       len(records),
        "total_in_dataset": len(df),
        "sorted_by":   sort_col,
    })


def _get_variable_statistics(args: dict, context: dict) -> str:
    df: pd.DataFrame = context["df"]
    var = args.get("variable_name", "")

    if var not in df.columns:
        available = context["objective_keys"] + context["decision_keys"]
        return json.dumps({
            "error":     f"Variable '{var}' not found in dataset.",
            "available": available,
        })

    series = pd.to_numeric(df[var], errors="coerce").dropna()
    if series.empty:
        return json.dumps({"error": f"Variable '{var}' has no numeric values."})

    unit = (context["objective_functions"].get(var) or {}).get("unit", "")
    return json.dumps({
        "variable": var,
        "unit":     unit,
        "count":    int(series.count()),
        "min":      round(float(series.min()), 4),
        "max":      round(float(series.max()), 4),
        "mean":     round(float(series.mean()), 4),
        "median":   round(float(series.median()), 4),
        "std":      round(float(series.std()), 4),
    })


def _get_tradeoff_summary(context: dict) -> str:
    df: pd.DataFrame   = context["df"]
    obj_keys: list     = context["objective_keys"]
    obj_fns: dict      = context["objective_functions"]

    summary = []
    for key in obj_keys:
        if key not in df.columns:
            continue
        series = pd.to_numeric(df[key], errors="coerce").dropna()
        if series.empty:
            continue
        best_idx = int(series.idxmin())
        unit = (obj_fns.get(key) or {}).get("unit", "")
        summary.append({
            "objective":        key,
            "unit":             unit,
            "best_value":       round(float(series.min()), 4),
            "worst_value":      round(float(series.max()), 4),
            "mean_value":       round(float(series.mean()), 4),
            "spread_pct":       round((series.max() - series.min()) / (abs(series.mean()) + 1e-9) * 100, 1),
            "best_solution_id": best_idx,
        })
    return json.dumps({
        "tradeoffs":       summary,
        "total_solutions": len(df),
    })


def _find_best_compromise(context: dict) -> str:
    df: pd.DataFrame = context["df"]
    obj_keys: list   = context["objective_keys"]
    dec_keys: list   = context["decision_keys"]
    weights: dict    = context["active_weights"]

    df = df.copy()
    norm_cols = []
    for k in obj_keys:
        if k not in df.columns:
            continue
        col = pd.to_numeric(df[k], errors="coerce")
        mn, mx = col.min(), col.max()
        df[f"_norm_{k}"] = (col - mn) / (mx - mn + 1e-9)
        norm_cols.append(f"_norm_{k}")

    if not norm_cols:
        return json.dumps({"error": "No numeric objectives found in dataset."})

    df["_compromise"] = sum(
        df[f"_norm_{k}"] * weights.get(k, 1.0)
        for k in obj_keys if f"_norm_{k}" in df.columns
    )
    best_idx = int(df["_compromise"].idxmin())
    display_cols = [c for c in ["Solution ID", *obj_keys, *dec_keys] if c in df.columns]
    best = df.loc[best_idx, display_cols].round(4).to_dict()

    return json.dumps({
        "best_compromise_solution": {str(k): v for k, v in best.items()},
        "solution_id":              best_idx,
        "note": "This solution minimises the normalised weighted sum across all objectives.",
    })


def _compare_solutions(args: dict, context: dict) -> str:
    df: pd.DataFrame = context["df"]
    obj_keys: list   = context["objective_keys"]
    dec_keys: list   = context["decision_keys"]

    id_a = args.get("solution_id_a")
    id_b = args.get("solution_id_b")

    if id_a not in df.index or id_b not in df.index:
        valid = df.index.tolist()[:10]
        return json.dumps({
            "error": f"Solution IDs {id_a} or {id_b} not found.",
            "valid_ids_sample": valid,
        })

    display_cols = [c for c in ["Solution ID", *obj_keys, *dec_keys] if c in df.columns]
    row_a = df.loc[id_a, display_cols].round(4).to_dict()
    row_b = df.loc[id_b, display_cols].round(4).to_dict()

    delta = {}
    for k in obj_keys:
        if k in row_a and k in row_b:
            try:
                delta[k] = round(float(row_a[k]) - float(row_b[k]), 4)
            except (TypeError, ValueError):
                pass

    return json.dumps({
        "solution_a":   {str(k): v for k, v in row_a.items()},
        "solution_b":   {str(k): v for k, v in row_b.items()},
        "delta_a_minus_b": delta,
        "note": "Negative delta means solution A is better (lower) for that objective.",
    })
