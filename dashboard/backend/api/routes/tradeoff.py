import logging

from flask import Blueprint, jsonify, request

import cache
from helpers.filtering import apply_filters, parse_weights
from helpers.labeling import get_filter_dimension_keys, get_scenario_dimension_keys
from helpers.lattice import build_scenario_lattice_payload

bp = Blueprint('tradeoff', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)


@bp.route('/tradeoff-lattice', methods=['GET'])
def get_tradeoff_lattice_data():
    use_case = request.args.get('use_case')
    if not use_case:
        return jsonify({"error": "Missing query param: use_case"}), 400
    try:
        data = cache.get_or_load(use_case)
        csv_data           = data["csv_data"]
        objective_functions = data["objective_functions"]
        decision_variables  = data["decision_variables"]
        objective_keys = list(objective_functions.keys())
        decision_keys  = list(decision_variables.keys())

        available_scenario_keys = get_scenario_dimension_keys(data, csv_data)
        filter_keys             = get_filter_dimension_keys(data, csv_data)

        requested = request.args.getlist('scenario_key')
        scenario_keys = ([k for k in requested if k in available_scenario_keys]
                         if requested else available_scenario_keys[:1])

        filtered = apply_filters(csv_data, {k: None for k in filter_keys}, request.args)
        weights  = parse_weights(request.args, objective_keys)

        if filtered.empty:
            return jsonify({"nodes": [], "edges": [], "objective_keys": objective_keys,
                            "scenario_keys": scenario_keys, "decision_keys": decision_keys,
                            "available_scenario_keys": available_scenario_keys,
                            "selected_scenario_keys": scenario_keys})

        payload = build_scenario_lattice_payload(
            filtered, scenario_keys, available_scenario_keys,
            decision_keys, objective_keys, objective_functions,
        )
        payload.update({
            "objective_keys":         objective_keys,
            "available_scenario_keys": available_scenario_keys,
            "selected_scenario_keys": scenario_keys,
        })
        return jsonify(payload)
    except Exception as e:
        logger.error("Error generating tradeoff lattice data: %s", e)
        return jsonify({"error": str(e)}), 500
