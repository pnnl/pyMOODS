"""TradeoffLattice payload builder."""
import numpy as np
import pandas as pd
import networkx as nx
from sklearn.decomposition import PCA
from tradeoff_lattice import TradeoffLattice, get_triangulation, test_all

from helpers.labeling import build_flat_label, ensure_unique_labels
from helpers.normalization import normalize_value

try:
    from umap import UMAP
except ImportError:
    UMAP = None


# ── Private helpers ────────────────────────────────────────────────────────────

def _build_embedding(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["x", "y"], index=frame.index)
    if len(frame) == 1:
        return pd.DataFrame([[0.0, 0.0]], index=frame.index, columns=["x", "y"])
    if len(frame) == 2:
        return pd.DataFrame([[0.0, -0.5], [0.0, 0.5]], index=frame.index, columns=["x", "y"])

    if UMAP is not None:
        try:
            coords = UMAP(spread=0.15).fit_transform(frame.values)
            return pd.DataFrame(coords[:, :2], index=frame.index, columns=["x", "y"])
        except Exception:
            pass

    n = min(2, frame.shape[1], len(frame))
    if n == 0:
        coords = np.zeros((len(frame), 2))
    else:
        coords = PCA(n_components=n).fit_transform(frame.values)
        if n == 1:
            coords = np.column_stack([coords[:, 0], np.zeros(len(frame))])
    return pd.DataFrame(coords[:, :2], index=frame.index, columns=["x", "y"])


def _build_cluster_graph(points: pd.DataFrame) -> nx.Graph:
    graph = nx.Graph()
    for label in points.index:
        graph.add_node(label, pos=points.loc[label].tolist())
    if len(points) < 2:
        return graph
    if len(points) == 2:
        graph.add_edge(points.index[0], points.index[1])
        return graph
    try:
        raw = get_triangulation(points.values)
        return nx.relabel_nodes(raw, dict(enumerate(points.index)))
    except Exception:
        for i in range(len(points) - 1):
            graph.add_edge(points.index[i], points.index[i + 1])
        return graph


# ── Public API ─────────────────────────────────────────────────────────────────

def build_scenario_lattice_payload(
    filtered_data: pd.DataFrame,
    scenario_keys: list,
    available_scenario_keys: list,
    decision_keys: list,
    objective_keys: list,
    objective_functions: dict,
) -> dict:
    empty = {"nodes": [], "edges": [], "ovars": objective_keys, "dvars": decision_keys,
             "scenario_keys": scenario_keys, "decision_keys": decision_keys}
    if filtered_data.empty:
        return empty

    frame = filtered_data.copy().reset_index(drop=True)
    row_labels = ensure_unique_labels([
        build_flat_label(row, available_scenario_keys) if available_scenario_keys else f"Scenario {i + 1}"
        for i, (_, row) in enumerate(frame.iterrows())
    ])
    frame.index = row_labels

    cluster_keys = scenario_keys[:] or available_scenario_keys[:1]
    cluster = pd.Series(
        [build_flat_label(row, cluster_keys) if cluster_keys else "All solutions"
         for _, row in frame.iterrows()],
        index=frame.index,
    )

    ascending = [k for k, v in objective_functions.items()
                 if isinstance(v, dict) and v.get("direction") == "maximize"]
    lattice = TradeoffLattice(df=frame, ovars=objective_keys, dvars=decision_keys, ascending=ascending)

    embed_frame = lattice.df[objective_keys].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    positions = _build_embedding(embed_frame)
    grouped = positions.groupby(cluster.loc[positions.index])
    centroids = grouped.mean()
    graph = _build_cluster_graph(centroids)

    for cluster_label, cluster_pts in grouped:
        graph.nodes[cluster_label]["index"] = pd.Index(cluster_pts.index)

    nodes = []
    for idx, cl in enumerate(centroids.index):
        members_idx = graph.nodes[cl]["index"]
        members = frame.loc[members_idx]
        x, y = (centroids.loc[cl, ["x", "y"]].tolist() if cl in centroids.index else (0.0, float(idx)))
        label_lines = [f"# {cl} ({len(members_idx)})"]

        gen_rows = lattice.generalizers.intersection(members_idx)
        if len(gen_rows):
            label_lines.append(f"generalizer ({len(gen_rows)})")

        spec_rows = lattice.specializers.intersection(members_idx)
        if len(spec_rows):
            for k, v in lattice.specialization.loc[spec_rows].sum(axis=0).items():
                if v > 0:
                    label_lines.append(f"+ {k} ({int(v)})")

        tradeoff_rows = lattice.tradeoff.index.intersection(members_idx)
        if len(tradeoff_rows):
            for k, v in lattice.tradeoff.loc[tradeoff_rows].sum(axis=0).items():
                if v > 0:
                    label_lines.append(f"- {k} ({int(v)})")

        nodes.append({
            "id": cl, "x": float(x), "y": float(y),
            "members": members_idx.tolist(), "label_lines": label_lines,
            "objectives": {k: normalize_value(pd.to_numeric(members[k], errors="coerce").median())
                           for k in objective_keys if k in members},
            "decisions":  {k: normalize_value(pd.to_numeric(members[k], errors="coerce").median())
                           for k in decision_keys  if k in members},
            "scenario":   {k: normalize_value(members.iloc[0][k]) for k in cluster_keys if k in members},
        })

    def _safe_float(v):
        n = normalize_value(v)
        if n is None:
            return None
        f = float(n)
        return None if not np.isfinite(f) else f

    edges = []
    for src, tgt in graph.edges():
        src_frame = lattice.df.loc[graph.nodes[src]["index"], objective_keys]
        tgt_frame = lattice.df.loc[graph.nodes[tgt]["index"], objective_keys]
        tests = test_all(src_frame, tgt_frame).reset_index().rename(columns={"index": "key"})
        edges.append({
            "source": str(src), "target": str(tgt),
            "tests": [{"key": str(t["key"]),
                       "direction":  _safe_float(t["direction"]),
                       "pvalue":     _safe_float(t["pvalue"]),
                       "magnitude":  _safe_float(t["magnitude"])}
                      for _, t in tests.iterrows()],
        })

    return {
        "nodes": nodes, "edges": edges,
        "ovars": objective_keys, "dvars": decision_keys,
        "scenario_keys": scenario_keys,
        "available_scenario_keys": available_scenario_keys,
        "selected_scenario_keys": cluster_keys,
        "decision_keys": decision_keys,
    }
