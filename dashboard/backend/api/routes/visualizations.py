import json
import logging

import pandas as pd
from dashlib.offshore_windfarm.vis import Visualizer
from flask import Blueprint, jsonify, request

import cache
from helpers.filtering import apply_filters, parse_weights
from helpers.viz import distplot_new, draw_clusters_scatterplot, generate_stacked_histogram

bp = Blueprint('visualizations', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)


@bp.route('/scatterplot', methods=['GET'])
def get_scatterplot():
    use_case = request.args.get('use_case')
    if not use_case:
        return jsonify({"error": "Missing query param: use_case"}), 400
    try:
        data = cache.get_or_load(use_case)
        vis = Visualizer(data=data["csv_data"],
                         data_ovars=list(data["objective_functions"].keys()),
                         data_dvars=list(data["decision_variables"].keys()))
        points = vis.joint_xy

        filtered = apply_filters(data["csv_data"], data["hyperparameters"], request.args)
        clusters = vis.df_clustered.loc[filtered.index, ["label"]]
        objective_keys = list(data["objective_functions"].keys())

        weights_input = request.args.get('weights')
        size = 10
        if weights_input:
            try:
                w = {k: float(v) for k, v in json.loads(weights_input).items()
                     if k in filtered[objective_keys].columns}
                if w:
                    size = filtered[list(w.keys())].mul(list(w.values())).sum(axis=1)
            except Exception as exc:
                logger.warning("Invalid weights JSON: %s", exc)

        fig = draw_clusters_scatterplot(
            full_dataset=filtered,
            points=points.loc[filtered.index],
            clusters=clusters,
            objective_keys=objective_keys,
            color_by=request.args.get('color_by'),
            size=size,
        )
        return jsonify({"scatterplot": fig.to_json(),
                        "config": {"displayModeBar": False, "responsive": True},
                        "color_by": request.args.get('color_by')})
    except Exception as e:
        logger.error("Error generating scatterplot: %s", e)
        return jsonify({"error": str(e)}), 500


@bp.route('/objective', methods=['GET'])
def get_objective_data():
    use_case = request.args.get('use_case')
    if not use_case:
        return jsonify({"error": "Missing query param: use_case"}), 400
    try:
        data = cache.get_or_load(use_case)
        objective_cols = list(data["objective_functions"].keys())
        filtered = apply_filters(data["csv_data"], data["hyperparameters"], request.args)

        weights_input = request.args.get('weights')
        weights = (json.loads(weights_input) if weights_input
                   else {col: 1 / len(objective_cols) for col in objective_cols})

        weighted_score = sum(filtered[col] * weights[col] for col in objective_cols).mean()
        return jsonify({"mean_weighted_score": weighted_score, "weights_used": weights,
                        "config": {"responsive": True}})
    except Exception as e:
        logger.error("Error generating objective data: %s", e)
        return jsonify({"error": str(e)}), 500


@bp.route('/objective-plot-data', methods=['GET'])
def get_objective_plot_data():
    use_case = request.args.get('use_case')
    if not use_case:
        return jsonify({"error": "Missing query param: use_case"}), 400
    try:
        data = cache.get_or_load(use_case)
        objective_cols = list(data["objective_functions"].keys())
        decision_cols  = list(data["decision_variables"].keys())

        filtered = apply_filters(data["csv_data"], data["hyperparameters"], request.args)
        weights  = parse_weights(request.args, objective_cols)

        filtered = filtered.copy()
        filtered['Weighted Sum'] = sum(filtered[col] * weights[col] for col in objective_cols)
        filtered = filtered.sort_values('Weighted Sum', ascending=False)

        def _dist(col):
            dist = filtered[col].tolist()
            return {"variable": col, "distribution": dist,
                    "selected": filtered.iloc[0][col], "max": max(dist) if dist else 1}

        return jsonify({
            "objectives": [_dist(c) for c in objective_cols],
            "decisions":  [_dist(c) for c in decision_cols],
        })
    except Exception as e:
        logger.error("Error fetching objective plot data: %s", e)
        return jsonify({"error": str(e)}), 500


@bp.route('/decision', methods=['GET'])
def get_decision_plot():
    use_case = request.args.get('use_case')
    if not use_case:
        return jsonify({"error": "Missing query param: use_case"}), 400
    try:
        data = cache.get_or_load(use_case)
        filtered = apply_filters(data["csv_data"], data["hyperparameters"], request.args)
        fig = generate_stacked_histogram(filtered)
        return jsonify({"plot": fig.to_json(),
                        "config": {"displayModeBar": False, "responsive": True, "showlegend": False}})
    except Exception as e:
        logger.error("Error generating decision plot: %s", e)
        return jsonify({"error": str(e)}), 500


@bp.route('/decision_space', methods=['GET'])
def get_decision_space_graph():
    use_case = request.args.get('use_case')
    if not use_case:
        return jsonify({"error": "Missing query param: use_case"}), 400
    try:
        data = cache.get_or_load(use_case)
        dvars = list(data["decision_variables"].keys())
        objective_col = list(data["objective_functions"].keys())[0]
        filtered = apply_filters(data["csv_data"], data["hyperparameters"], request.args).copy()
        filtered["ovar"] = objective_col
        fig = distplot_new(filtered, dvars)
        return jsonify({"plot": fig.to_json(),
                        "config": {"displayModeBar": False, "responsive": True}})
    except Exception as e:
        logger.error("Error generating decision space graph: %s", e)
        return jsonify({"error": str(e)}), 500
