import logging

from flask import Blueprint, jsonify, request

import cache
from helpers.filtering import apply_filters

bp = Blueprint('parameters', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)


@bp.route('/parameters', methods=['GET'])
def get_parameters():
    use_case = request.args.get('use_case')
    if not use_case:
        return jsonify({"error": "Missing query param: use_case"}), 400
    try:
        data = cache.get_or_load(use_case)
        result = [
            {"key": key, "name": info.get("name", key), "values": info["values"], "is_clusterable": True}
            for key, info in data["hyperparameters"].items()
            if isinstance(info, dict) and "values" in info and isinstance(info["values"], list)
        ]
        return jsonify(result)
    except Exception as e:
        logger.error("Error fetching parameters: %s", e)
        return jsonify({"error": str(e)}), 500


@bp.route('/lmp', methods=['GET'])
def get_lmp_data():
    use_case = request.args.get('use_case')
    if not use_case:
        return jsonify({"error": "Missing query param: use_case"}), 400
    try:
        data = cache.get_or_load(use_case)
        scenario_data = data.get("scenario_data")
        if scenario_data is None:
            return jsonify({"data": []})
        filtered = apply_filters(scenario_data, data["hyperparameters"], request.args)
        return jsonify({"data": filtered.to_dict(orient='records')})
    except Exception as e:
        logger.error("Error fetching LMP data: %s", e)
        return jsonify({"error": str(e)}), 500
