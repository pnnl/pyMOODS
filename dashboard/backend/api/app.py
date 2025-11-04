import sys
import os

# Add the dashboard directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
import plotly.colors as pc
from scipy.spatial import ConvexHull
from scipy.spatial.qhull import QhullError
from sklearn.cluster import HDBSCAN

# Import specific modules from your dashboard library
from dashlib.offshore_windfarm.vis import Visualizer
from dashlib.components import blank_figure

app = Flask(__name__)
CORS(app)  # Enable CORS to allow requests from the React app
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow any origin for development

# Load data for the visualizations
CSV_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "v2_test_summary.csv")
csv_data = pd.read_csv(CSV_FILE_PATH)

# Initialize visualization tools
ovars = ['objective']
dvars = ['size', 'cable']
vis_obj = Visualizer(data=csv_data, data_ovars=ovars, data_dvars=dvars)
points = vis_obj.joint_xy

kwargs = dict(
    threshold=0.5,
    clu=HDBSCAN(
        cluster_selection_epsilon=1.,
        min_cluster_size=10
    ),
    drop_intermediate=False
)

clusters = vis_obj.get_overlapping_clusters(**kwargs)
initial_clusters = csv_data[['location']]

def get_convex_hull(points):
    # Drop duplicate points to avoid errors
    unique_points = points.drop_duplicates()

    # ConvexHull requires at least 3 points in 2D, 4 in 3D
    min_points = max(3, unique_points.shape[1] + 1)
    if unique_points.shape[0] < min_points:
        return unique_points  # Return all points if hull can't be computed

    try:
        hull = ConvexHull(unique_points.values)  # Compute convex hull
        return unique_points.iloc[hull.vertices]  # Return hull points
    except QhullError:
        return unique_points  # Return all points if convex hull fails

def draw_clusters_scatterplot(clusters, points, selected_indices=None):
    clusters = pd.get_dummies(clusters.iloc[:, 0], dtype=int).replace(0, -1)
    fig = go.Figure()
    no_cluster_mask = ~points.index.isin(clusters.index)
    no_cluster_df = points[no_cluster_mask]

    fig.add_trace(go.Scatter(x=no_cluster_df[0], y=no_cluster_df[1], mode='markers', marker=dict(color='lightgray', size=4, opacity=0.1), name='unassigned'))
    for i, c in enumerate(clusters):
        ec = pc.hex_to_rgb(px.colors.qualitative.D3[i]) + (1.0,)
        hulls = [
            get_convex_hull(dfk)
            for k, dfk in points.groupby(clusters[c])
            if k != -1
        ]
        for j in range(len(hulls)):
            x_coords = hulls[j][0].to_list()
            y_coords = hulls[j][1].to_list()
            fig.add_trace(go.Scatter(x=x_coords+[x_coords[0]], y=y_coords+[y_coords[0]], mode="lines", fill="toself", fillcolor=f"rgba{ec[:3] + (0.2,)}", line=dict(color=f"rgba{ec}"), showlegend=False))

        mask = clusters[c] != -1
        # more than one item in that row with value other than -1
        multi_cluster_mask = (clusters[clusters.columns] != -1).sum(axis=1) > 1

        if selected_indices is not None:
            # mask for checking any data in subset created in dist plot
            selected_mask = clusters.index.isin(selected_indices)
            unselected_single_cluster_df = points.loc[clusters.index][mask & ~multi_cluster_mask & ~selected_mask]
            fig.add_trace(go.Scatter(x=unselected_single_cluster_df[0], y=unselected_single_cluster_df[1], mode='markers', marker=dict(color='lightgray', size=5, opacity=0.5), name=f'{c} (unselected)'))

            selected_single_cluster_df = points.loc[clusters.index][mask & ~multi_cluster_mask & selected_mask]
            fig.add_trace(go.Scatter(x=selected_single_cluster_df[0], y=selected_single_cluster_df[1], mode='markers', marker=dict(color=f'rgba{ec}', size=6), name=f'{c} (selected)'))

            # # points with multiple clusters
            unselected_multi_cluster_df = points.loc[clusters.index][multi_cluster_mask & ~selected_mask]
            fig.add_trace(go.Scatter(x=unselected_multi_cluster_df[0], y=unselected_multi_cluster_df[1], mode='markers', marker=dict(color='lightgray', size=5, opacity=0.5), name='multi_cluster (unselected)', showlegend=False if i > 0 else True))

            selected_multi_cluster_df = points.loc[clusters.index][multi_cluster_mask & selected_mask]
            fig.add_trace(go.Scatter(x=selected_multi_cluster_df[0], y=selected_multi_cluster_df[1], mode='markers', marker=dict(opacity=1, color='black', size=6), name='multi_cluster (selected)', showlegend=False if i > 0 else True))
        else:
            # excluding points with multiple clusters
            remaining_df = points.loc[clusters.index][mask & ~multi_cluster_mask]
            fig.add_trace(go.Scatter(x=remaining_df[0], y=remaining_df[1], mode='markers', marker=dict(color=f'rgba{ec}', size=5), name=c))

            # points with multiple clusters
            multi_cluster_df = points.loc[clusters.index][multi_cluster_mask]
            fig.add_trace(go.Scatter(x=multi_cluster_df[0], y=multi_cluster_df[1], mode='markers', marker=dict(color='black', size=5), name='multiple_cluster', showlegend=False if i > 0 else True))

    fig.update_layout(
        margin=dict(t=20, b=20),
        legend=dict(
            x=1.03,
            bordercolor='#d3d3d3',
            borderwidth=1,
            bgcolor='white',
            font=dict(
                size=14  # Set the font size of the legend items
            ),
            traceorder='normal',
            title=dict(text=' cluster', font=dict(size=14))
        ),
        template="plotly_white",
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showticklabels=False, showgrid=False)
    )
    return fig

def generate_objective_graph_data(data):
    objective_col = 'objective'  # Use the standard column name from the data
    if not data.empty:
        objective_mean = float(data[objective_col].mean())
        objective_std = float(data[objective_col].std())
        # Print debug info to server console
        print(f"Calculated objective data - mean: {objective_mean}, std: {objective_std}")
    else:
        objective_mean = 0
        objective_std = 0
        print("Warning: No data available for objective calculation")
    
    return {
        "mean": objective_mean,
        "std": objective_std,
        "title": "objective"
    }

@app.route('/api/scatterplot', methods=['GET'])
def get_scatterplot():
    # Get query parameters (optional)
    location = request.args.getlist('location')
    technology = request.args.getlist('technology')
    duration = request.args.getlist('duration')
    power = request.args.getlist('power')
    
    # Filter data based on parameters if provided
    filtered_data = csv_data.copy()
    
    if location:
        filtered_data = filtered_data[filtered_data['location'].isin(location)]
    if technology:
        filtered_data = filtered_data[filtered_data['technology'].isin(technology)]
    if duration:
        filtered_data = filtered_data[filtered_data['duration'].isin(duration)]
    if power:
        filtered_data = filtered_data[filtered_data['power'].isin(power)]
    
    # Update clusters and points based on filtered data
    updated_clusters = filtered_data[['location']]
    updated_points = points.loc[filtered_data.index]
    
    # Generate scatterplot
    fig = draw_clusters_scatterplot(updated_clusters, updated_points)
    
    # Return the full figure data as JSON
    return jsonify({
        "scatterplot": fig.to_json(),
        "config": {
            "displayModeBar": False,
            "responsive": True
        }
    })

@app.route('/api/objective', methods=['GET'])
def get_objective_data():
    # Get query parameters (optional)
    location = request.args.getlist('location')
    technology = request.args.getlist('technology')
    duration = request.args.getlist('duration')
    power = request.args.getlist('power')
    
    # Filter data based on parameters if provided
    filtered_data = csv_data.copy()
    
    if location:
        filtered_data = filtered_data[filtered_data['location'].isin(location)]
    if technology:
        filtered_data = filtered_data[filtered_data['technology'].isin(technology)]
    if duration:
        filtered_data = filtered_data[filtered_data['duration'].isin(duration)]
    if power:
        filtered_data = filtered_data[filtered_data['power'].isin(power)]
    
    # Generate objective data
    objective_data = generate_objective_graph_data(filtered_data)
    
    # Print the response for debugging
    print(f"Sending objective data response: {objective_data}")
    
    return jsonify(objective_data)

@app.route('/api/parameters', methods=['GET'])
def get_parameters():
    # Return available parameter options for filtering
    return jsonify({
        "location": sorted(csv_data.location.unique().tolist()),
        "technology": sorted(csv_data.technology.unique().tolist()),
        "duration": sorted(csv_data.duration.unique().tolist()),
        "power": sorted(csv_data.power.unique().tolist())
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)