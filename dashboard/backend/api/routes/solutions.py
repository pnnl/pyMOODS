import json
import logging
from collections import OrderedDict

import pandas as pd
from dashlib.offshore_windfarm.vis import Visualizer
from flask import Blueprint, Response, jsonify, request

import cache
from helpers.filtering import apply_column_filters, apply_filters, parse_weights
from helpers.normalization import order_solutions_for_display
from helpers.ranking import (
    build_filtered_solution_ranks,
    build_rank_dict,
    build_solution_rank_key,
    compute_topsis,
    compute_vikor,
    create_lattice,
    get_objective_rank_frame,
)

bp = Blueprint('solutions', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

_FILTER_SKIP = frozenset({'weight_', 'use_case', 'min_specializers', 'top_n'})


def _skip(key: str) -> bool:
    return key in _FILTER_SKIP or key.startswith('weight_')


@bp.route('/solutions', methods=['GET'])
def get_weighted_solutions():
    use_case = request.args.get('use_case')
    if not use_case:
        return jsonify({"error": "Missing query param: use_case"}), 400
    try:
        data    = cache.get_or_load(use_case)
        ovars   = list(data["objective_functions"].keys())
        dvars   = list(data["decision_variables"].keys())
        obj_units = {k: (v.get("unit") if isinstance(v, dict) else None)
                     for k, v in data["objective_functions"].items()}
        obj_directions = {k: (v.get("direction", "minimize") if isinstance(v, dict) else "minimize")
                          for k, v in data["objective_functions"].items()}

        visualizer_dvars = [c for c in dvars
                            if c in data["csv_data"].columns
                            and pd.to_numeric(data["csv_data"][c], errors='coerce').notna().all()
                            ] or ovars[:1]

        vis = Visualizer(data=data["csv_data"], data_ovars=ovars, data_dvars=visualizer_dvars)
        filtered = apply_filters(data["csv_data"], data["hyperparameters"], request.args)

        points   = vis.joint_xy.loc[filtered.index]
        clusters = vis.df_clustered.loc[filtered.index, ["label"]]
        filtered = (pd.concat([filtered, points, clusters], axis=1)
                    .rename(columns={0: 'x_coord', 1: 'y_coord'}))

        weights = parse_weights(request.args, ovars)
        filtered = filtered.copy()
        filtered['Weighted Sum'] = sum(filtered[col] * weights[col] for col in ovars)

        rank_frame = get_objective_rank_frame(filtered, data["objective_functions"], data["decision_variables"])
        ranks      = build_rank_dict(rank_frame)

        display_cols = [c for c in filtered.columns if c != 'File Name']
        solutions = [OrderedDict([(c, row[c]) for c in display_cols])
                     for _, row in filtered.iterrows()]

        return Response(
            json.dumps({
                "solutions":         solutions,
                "ranks":             ranks,
                "weights_used":      weights,
                "index_keys":        ['Solution ID'],
                "objective_keys":    ovars,
                "objective_units":      obj_units,
                "objective_directions": obj_directions,
                "decision_keys":        dvars,
                "hyperparameter_keys": list(data["hyperparameters"].keys()),
                "additional_cols":   ['Weighted Sum'],
            }, sort_keys=False),
            mimetype='application/json',
        )
    except Exception as e:
        logger.error("Error fetching weighted solutions: %s", e)
        return jsonify({"error": str(e)}), 500


@bp.route('/project', methods=['POST'])
def get_projection_data():
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "No JSON payload received"}), 400
        use_case = payload.get('use_case')
        if not use_case:
            return jsonify({"error": "Missing field: use_case"}), 400
        solution_ids = payload.get("solution_ids")
        if not solution_ids:
            return jsonify({"error": "Missing field: solution_ids"}), 400

        data = cache.get_or_load(use_case)
        filtered = pd.DataFrame(solution_ids)
        ovars = list(data["objective_functions"].keys())
        dvars = list(data["decision_variables"].keys())

        vis = Visualizer(data=filtered, data_ovars=ovars, data_dvars=dvars)
        points = vis.joint_xy.loc[filtered.index]
        points.columns = ["x_coord", "y_coord"]

        result: dict = {"x": points[0].tolist(), "y": points[1].tolist()}
        color_by = payload.get("color_by")
        if color_by and color_by in filtered.columns:
            result["colorValues"] = filtered[color_by].fillna("Unknown").tolist()
        return jsonify(result)
    except Exception as e:
        logger.error("Error generating projections: %s", e)
        return jsonify({"error": str(e)}), 500


@bp.route('/specializers', methods=['GET'])
def get_specializers():
    use_case = request.args.get('use_case')
    if not use_case:
        return jsonify({"error": "use_case parameter is required"}), 400
    try:
        min_n   = int(request.args.get('min_specializers', 5))
        data    = cache.get_or_load(use_case)
        ovars   = list(data["objective_functions"].keys())
        dvars   = list(data["decision_variables"].keys())
        filtered = apply_column_filters(data["csv_data"], {k for k in request.args if _skip(k)}, request.args)

        if filtered.empty:
            return jsonify({"solutions": [], "ranks": {}, "specializers_count": 0,
                            "objective_keys": ovars, "decision_keys": dvars})

        lattice = create_lattice(filtered, data["objective_functions"], data["decision_variables"])
        specialists = filtered.loc[lattice.specializers].copy()
        if len(specialists) > min_n:
            specialists = specialists.head(min_n)

        solutions = order_solutions_for_display(specialists)
        ranks = build_filtered_solution_ranks(
            filtered, data["objective_functions"], data["decision_variables"],
            specialists, key_builder=build_solution_rank_key,
        )
        spec_matrix = (lattice.specialization.loc[specialists.index].to_dict()
                       if len(specialists) > 0 else {})

        return Response(
            json.dumps({"solutions": solutions, "ranks": ranks,
                        "specializers_count": len(specialists),
                        "total_solutions": len(filtered),
                        "objective_keys": ovars, "decision_keys": dvars,
                        "specialization_matrix": spec_matrix}, sort_keys=False),
            mimetype='application/json',
        )
    except Exception as e:
        logger.error("Error in specializers endpoint: %s", e)
        return jsonify({"error": str(e)}), 500


@bp.route('/generalizers', methods=['GET'])
def get_generalizers():
    use_case = request.args.get('use_case')
    if not use_case:
        return jsonify({"error": "use_case parameter is required"}), 400
    try:
        top_n = max(1, int(request.args.get('top_n', 1)))
        data    = cache.get_or_load(use_case)
        ovars   = list(data["objective_functions"].keys())
        dvars   = list(data["decision_variables"].keys())
        obj_units = {k: (v.get("unit") if isinstance(v, dict) else None)
                     for k, v in data["objective_functions"].items()}
        hyperparameter_keys = list(data.get("hyperparameters", {}).keys())
        input_parameter_keys = list(data.get("input_parameters", {}).keys())
        filtered = apply_column_filters(data["csv_data"], {k for k in request.args if _skip(k)}, request.args)

        if filtered.empty:
            return jsonify({"solutions": [], "ranks": {}, "generalizers_count": 0,
                            "objective_keys": ovars, "decision_keys": dvars,
                            "objective_units": obj_units,
                            "hyperparameter_keys": hyperparameter_keys,
                            "input_parameter_keys": input_parameter_keys,
                            "specialization_matrix": {}, "tradeoff_matrix": {},
                            "solution_details_by_key": {}})

        lattice = create_lattice(filtered, data["objective_functions"], data["decision_variables"])
        ranked_idx = lattice.rank.index
        generalized = (
            filtered.loc[ranked_idx[:top_n]].copy()
            if len(ranked_idx) > 0
            else filtered.head(top_n).copy()
        )

        solutions = order_solutions_for_display(generalized)
        ranks = build_filtered_solution_ranks(
            filtered, data["objective_functions"], data["decision_variables"],
            generalized, key_builder=build_solution_rank_key,
        )

        most_generalizer_rank_key = None
        if len(generalized) > 0:
            first_idx = generalized.index[0]
            most_generalizer_rank_key = build_solution_rank_key(generalized.loc[first_idx], first_idx)

        specialization_frame = (
            lattice.specialization
            .reindex(index=generalized.index, columns=ovars, fill_value=False)
            .fillna(False)
            .astype(bool)
        )
        tradeoff_frame = (
            lattice.tradeoff
            .reindex(index=generalized.index, columns=ovars, fill_value=False)
            .fillna(False)
            .astype(bool)
        )

        specialization_matrix = {}
        tradeoff_matrix = {}
        rank_keys = []
        for idx, row in generalized.iterrows():
            rank_key = build_solution_rank_key(row, idx)
            rank_keys.append(rank_key)
            specialization_matrix[rank_key] = {
                obj: bool(specialization_frame.loc[idx, obj])
                for obj in ovars
            }
            tradeoff_matrix[rank_key] = {
                obj: bool(tradeoff_frame.loc[idx, obj])
                for obj in ovars
            }

        solution_details_by_key = {
            key: solutions[i]
            for i, key in enumerate(rank_keys)
            if i < len(solutions)
        }

        return Response(
            json.dumps({"solutions": solutions, "ranks": ranks,
                        "generalizers_count": len(generalized),
                        "requested_top_n": top_n,
                        "total_solutions": len(filtered),
                        "objective_keys": ovars, "decision_keys": dvars,
                        "objective_units": obj_units,
                        "hyperparameter_keys": hyperparameter_keys,
                        "input_parameter_keys": input_parameter_keys,
                        "specialization_matrix": specialization_matrix,
                        "tradeoff_matrix": tradeoff_matrix,
                        "solution_details_by_key": solution_details_by_key,
                        "most_generalizer_rank_key": most_generalizer_rank_key,
                        "is_most_generalized": True}, sort_keys=False),
            mimetype='application/json',
        )
    except Exception as e:
        logger.error("Error in generalizers endpoint: %s", e)
        return jsonify({"error": str(e)}), 500


@bp.route('/mcdm-solutions', methods=['GET'])
def get_mcdm_solutions():
    """Return solutions ranked by a chosen MCDM technique.

    Supported techniques: weighted_sum, topsis, vikor.
    The generalizer_specializer technique is served by /generalizers and /specializers.
    """
    use_case = request.args.get('use_case')
    if not use_case:
        return jsonify({"error": "use_case parameter is required"}), 400

    technique = request.args.get('technique', 'weighted_sum')
    top_n = int(request.args.get('top_n', 10))

    _SCORE_META = {
        'weighted_sum': ('mcdm_score', 'Weighted Sum', True),   # ascending sort
        'topsis':       ('mcdm_score', 'TOPSIS Score', False),  # descending sort
        'vikor':        ('mcdm_score', 'VIKOR Q',      True),   # ascending sort
    }
    if technique not in _SCORE_META:
        return jsonify({"error": f"Unknown technique: {technique}"}), 400

    score_col, score_label, sort_ascending = _SCORE_META[technique]

    try:
        data    = cache.get_or_load(use_case)
        ovars   = list(data["objective_functions"].keys())
        dvars   = list(data["decision_variables"].keys())
        obj_units = {k: (v.get("unit") if isinstance(v, dict) else None)
                     for k, v in data["objective_functions"].items()}
        obj_directions = {k: (v.get("direction", "minimize") if isinstance(v, dict) else "minimize")
                          for k, v in data["objective_functions"].items()}

        filtered = apply_column_filters(
            data["csv_data"],
            {k for k in request.args if _skip(k)},
            request.args,
        )
        if filtered.empty:
            return jsonify({
                "solutions": [], "technique": technique, "score_label": score_label,
                "objective_keys": ovars, "decision_keys": dvars,
            })

        weights = parse_weights(request.args, ovars)
        df = filtered.copy()

        if technique == 'topsis':
            df[score_col] = compute_topsis(filtered, ovars, obj_directions, weights)
        elif technique == 'vikor':
            df[score_col] = compute_vikor(filtered, ovars, obj_directions, weights)
        else:  # weighted_sum — same formula as /api/solutions for consistency
            df[score_col] = sum(filtered[col] * weights[col] for col in ovars)

        ranked = df.sort_values(score_col, ascending=sort_ascending).head(top_n)
        solutions = order_solutions_for_display(ranked)

        return Response(
            json.dumps({
                "solutions":           solutions,
                "technique":           technique,
                "score_label":         score_label,
                "objective_keys":      ovars,
                "decision_keys":       dvars,
                "objective_units":     obj_units,
                "objective_directions": obj_directions,
            }, sort_keys=False),
            mimetype='application/json',
        )
    except Exception as e:
        logger.error("Error in mcdm-solutions endpoint: %s", e)
        return jsonify({"error": str(e)}), 500
