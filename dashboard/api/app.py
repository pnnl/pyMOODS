import sys
import os

# Add the dashboard directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
# from dashlib.offshore_windfarm.vis import Visualizer
from dashlib.offshore_windfarm.screen3 import draw_clusters_scatterplot_json, clusters, points

app = Flask(__name__)
CORS(app)  # Enable CORS to allow requests from the React app
CORS(app, resources={r"/*": {"origins": "http://localhost:8080"}})

@app.route('/api/scatterplot', methods=['GET'])
def get_scatterplot():
    # Generate the scatterplot JSON
    scatterplot_figure = draw_clusters_scatterplot_json(clusters, points)
    scatterplot_json = scatterplot_figure.to_json()  # Convert the figure to JSON
    return jsonify({"scatterplot": scatterplot_json})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# # Load data and initialize Visualizer
# CSV_FILE_PATH = "../data/v2_test_summary.csv"
# data = pd.read_csv(CSV_FILE_PATH)
# ovars = ['objective']
# dvars = ['size', 'cable']
# visualizer = Visualizer(data=data, data_ovars=ovars, data_dvars=dvars)

# @app.route('/api/plot/time_series', methods=['GET'])
# def get_time_series():
#     location = request.args.get('location', 'MOSSLAND')
#     fig = visualizer.generate_time_series(location)
#     return jsonify(fig.to_dict())

# @app.route('/api/plot/fairness_index', methods=['GET'])
# def get_fairness_index():
#     fig = visualizer.generate_fairness_index()
#     return jsonify(fig.to_dict())

# @app.route('/api/plot/hypergraph', methods=['GET'])
# def get_hypergraph():
#     H, nodes, df = visualizer.create_hypergraph()
#     fig = visualizer.show_collapsed_hypergraph(H, nodes, cmap={})
#     return jsonify(fig.to_dict())

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)