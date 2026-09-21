import logging
import os

from flask import Blueprint, jsonify, request

import cache
from config import DEMO_DATA_DIR

bp = Blueprint('case_studies', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)


@bp.route('/case-studies', methods=['GET'])
def get_case_studies():
    files = [f.split(".")[0] for f in os.listdir(DEMO_DATA_DIR) if f.endswith('.json')]
    return jsonify({"files": files})


@bp.route('/init', methods=['GET'])
def get_init_data():
    use_case = request.args.get('use_case')
    if not use_case:
        return jsonify({"error": "Missing query param: use_case"}), 400
    try:
        data = cache.get_or_load(use_case)
        hyperparams = data["hyperparameters"]
        filter_options = [
            {"key": key, "name": info.get("name", key), "values": info["values"], "is_clusterable": True}
            for key, info in hyperparams.items()
            if isinstance(info, dict) and "values" in info and isinstance(info["values"], list)
        ]
        objective_cols = list(data["objective_functions"].keys())
        return jsonify({
            "filters": filter_options,
            "objectives": {col: 1 for col in objective_cols},
        })
    except Exception as e:
        logger.error("Error initializing data: %s", e)
        return jsonify({"error": str(e)}), 500
