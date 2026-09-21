"""
Entry point for the PyMOODS React API.

Run with:
    LLM_API_KEY=<your-key> python react_api.py

Module layout:
    config.py          — paths, AI constants
    cache.py           — in-memory case-study cache
    helpers/           — pure utility functions (no Flask)
      filtering.py     — apply_filters, parse_weights
      normalization.py — value conversion, solution display ordering
      ranking.py       — TradeoffLattice-based objective ranking
      labeling.py      — scenario / dimension labeling
      viz.py           — Plotly figure builders
      lattice.py       — tradeoff lattice payload
      ai_client.py     — PNNL incubator client + system prompts
    routes/            — Flask Blueprints (one file per concern)
      case_studies.py  — /api/case-studies, /api/init
      visualizations.py— /api/scatterplot, /api/objective, /api/objective-plot-data,
                          /api/decision, /api/decision_space
      solutions.py     — /api/solutions, /api/project,
                          /api/specializers, /api/generalizers
      parameters.py    — /api/parameters, /api/lmp
      tradeoff.py      — /api/tradeoff-lattice
      chat.py          — /api/chat/init, /api/chat
"""
import os
import sys
import requests

# Must be set before numba / sklearn are imported
os.environ.setdefault('NUMBA_THREADING_LAYER', 'omp')
os.environ.setdefault('NUMBA_NUM_THREADS', '1')

# Make this directory importable so helpers/ and routes/ resolve correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# config is imported first — it extends sys.path with dashboard/ and pymoods/
import config  # noqa: F401  (side-effect: path setup)

import json

from flask import Flask, jsonify, request
from flask_cors import CORS

from routes.case_studies  import bp as case_studies_bp
from routes.chat          import bp as chat_bp
from routes.parameters    import bp as parameters_bp
from routes.solutions     import bp as solutions_bp
from routes.tradeoff      import bp as tradeoff_bp
from routes.visualizations import bp as visualizations_bp

app = Flask(__name__)
CORS(app, origins="*", allow_headers="*", methods="*", supports_credentials=False)

for _bp in (case_studies_bp, visualizations_bp, solutions_bp,
            parameters_bp, tradeoff_bp, chat_bp):
    app.register_blueprint(_bp)


@app.route('/api/network-graph', methods=['GET'])
def get_network_graph_data():
    filename = request.args.get('file')
    if not filename:
        return jsonify({"error": "Missing query param: file"}), 400

    # Validate filename to prevent path traversal
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.')
    if not all(c in allowed_chars for c in filename) or '..' in filename:
        return jsonify({"error": "Invalid filename"}), 400

    if not filename.endswith('.json'):
        return jsonify({"error": "Only JSON files are allowed"}), 400

    schema_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "demo_data", "network_graph_json_schema"
    )
    filepath = os.path.join(schema_dir, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": f"File not found: {filename}"}), 404

    with open(filepath, 'r') as f:
        data = json.load(f)

    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True, threaded=False, host="0.0.0.0", port=8080)
