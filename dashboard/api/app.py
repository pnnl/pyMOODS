import sys, os, json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
import plotly.colors as pc
from scipy.spatial import ConvexHull, QhullError
from sklearn.cluster import HDBSCAN
from flask_caching import Cache

from dashlib.offshore_windfarm.vis import Visualizer

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure cache - add this after creating the Flask app
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# Paths to the data files
MOCODO_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mocodo24_v2_test.json")
CSV_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "v2_test_summary.csv")

# Load and parse mocodo.json
with open(MOCODO_JSON_PATH, 'r') as file:
    mocodo_data = json.load(file)

hyperparameters = mocodo_data["hyperparameters"]
input_parameters = mocodo_data["input_parameters"]
objective_functions = mocodo_data["objective_functions"]
decision_variables = mocodo_data["decision_variables"]

ovars = [list(objective_functions.keys())[0]]
dvars = list(decision_variables.keys())

# Load data for the visualizations
csv_data = pd.read_csv(CSV_FILE_PATH)

# Convert CSV to JSON
csv_data_json = csv_data.to_dict(orient="records")

# Initialize visualization tools
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

# Function to get the convex hull of a set of points for the cluster scatter plot
def get_convex_hull(points):
    unique_points = points.drop_duplicates()

    min_points = max(3, unique_points.shape[1] + 1)
    if unique_points.shape[0] < min_points:
        return unique_points

    try:
        hull = ConvexHull(unique_points.values)
        return unique_points.iloc[hull.vertices]
    except QhullError:
        return unique_points

# Function to draw the offshore windfarm cluster scatter plot
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
        multi_cluster_mask = (clusters[clusters.columns] != -1).sum(axis=1) > 1

        if selected_indices is not None:
            selected_mask = clusters.index.isin(selected_indices)
            unselected_single_cluster_df = points.loc[clusters.index][mask & ~multi_cluster_mask & ~selected_mask]
            fig.add_trace(go.Scatter(x=unselected_single_cluster_df[0], y=unselected_single_cluster_df[1], mode='markers', marker=dict(color='lightgray', size=5, opacity=0.5), name=f'{c} (unselected)'))

            selected_single_cluster_df = points.loc[clusters.index][mask & ~multi_cluster_mask & selected_mask]
            fig.add_trace(go.Scatter(x=selected_single_cluster_df[0], y=selected_single_cluster_df[1], mode='markers', marker=dict(color=f'rgba{ec}', size=6), name=f'{c} (selected)'))

            unselected_multi_cluster_df = points.loc[clusters.index][multi_cluster_mask & ~selected_mask]
            fig.add_trace(go.Scatter(x=unselected_multi_cluster_df[0], y=unselected_multi_cluster_df[1], mode='markers', marker=dict(color='lightgray', size=5, opacity=0.5), name='multi_cluster (unselected)', showlegend=False if i > 0 else True))

            selected_multi_cluster_df = points.loc[clusters.index][multi_cluster_mask & selected_mask]
            fig.add_trace(go.Scatter(x=selected_multi_cluster_df[0], y=selected_multi_cluster_df[1], mode='markers', marker=dict(opacity=1, color='black', size=6), name='multi_cluster (selected)', showlegend=False if i > 0 else True))
        else:
            remaining_df = points.loc[clusters.index][mask & ~multi_cluster_mask]
            fig.add_trace(go.Scatter(x=remaining_df[0], y=remaining_df[1], mode='markers', marker=dict(color=f'rgba{ec}', size=5), name=c))

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

# Function to calculate the mean and std and display the objective space
def generate_objective_graph_data(data):
    # Get the objective column name from the mocodo data
    objective_col = list(objective_functions.keys())[0]
    objective_title = objective_functions[objective_col]['name']
    
    if not data.empty:
        objective_mean = data[objective_col].mean()
        objective_std = data[objective_col].std()
    else:
        objective_mean = 0
        objective_std = 0
    
    return {
        "mean": objective_mean,
        "std": objective_std,
        "title": objective_title
    }

# Add these new functions to pre-calculate statistics
def calculate_all_statistics():
    """Pre-calculate statistics for all possible parameter combinations."""
    objective_col = list(objective_functions.keys())[0]
    objective_title = objective_functions[objective_col]['name']
    
    all_locations = csv_data.location.unique().tolist()
    all_technologies = csv_data.technology.unique().tolist()
    all_durations = csv_data.duration.unique().tolist()
    all_powers = csv_data.power.unique().tolist()
    
    stats_cache = {}
    
    # Calculate overall stats
    overall_mean = csv_data[objective_col].mean()
    overall_std = csv_data[objective_col].std()
    stats_cache['all'] = {
        "mean": float(overall_mean),
        "std": float(overall_std),
        "title": objective_title
    }
    
    # Calculate stats for each parameter combination
    param_combinations = {
        'location': all_locations,
        'technology': all_technologies, 
        'duration': all_durations,
        'power': all_powers
    }
    
    # Pre-calculate for individual parameters
    for param, values in param_combinations.items():
        for value in values:
            filtered = csv_data[csv_data[param] == value]
            key = f"{param}:{value}"
            stats_cache[key] = {
                "mean": float(filtered[objective_col].mean()),
                "std": float(filtered[objective_col].std()),
                "title": objective_title
            }
    
    # Handle common combinations (select a reasonable subset to avoid combinatorial explosion)
    for loc in all_locations:
        for tech in all_technologies:
            filtered = csv_data[(csv_data['location'] == loc) & (csv_data['technology'] == tech)]
            if not filtered.empty:
                key = f"location:{loc},technology:{tech}"
                stats_cache[key] = {
                    "mean": float(filtered[objective_col].mean()),
                    "std": float(filtered[objective_col].std()),
                    "title": objective_title
                }
    
    return stats_cache

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

@app.route('/api/objective-stats', methods=['GET'])
@cache.cached(timeout=3600)  # Cache for 1 hour
def get_all_objective_stats():
    """Return pre-calculated statistics for all parameter combinations."""
    return jsonify(calculate_all_statistics())

# Modify the existing objective endpoint to use the cached stats when possible
@app.route('/api/objective', methods=['GET'])
def get_objective_data():
    # Get query parameters (optional)
    location = request.args.getlist('location')
    technology = request.args.getlist('technology')
    duration = request.args.getlist('duration')
    power = request.args.getlist('power')
    
    # For simple cases, try to use pre-calculated stats
    if len(location) == 1 and not technology and not duration and not power:
        # Single location filter
        cache_key = f"location:{location[0]}"
        cached_stats = calculate_all_statistics().get(cache_key)
        if cached_stats:
            return jsonify(cached_stats)
    
    elif len(location) == 1 and len(technology) == 1 and not duration and not power:
        # Location + technology filter
        cache_key = f"location:{location[0]},technology:{technology[0]}"
        cached_stats = calculate_all_statistics().get(cache_key)
        if cached_stats:
            return jsonify(cached_stats)
    
    # For other combinations, calculate on-the-fly
    filtered_data = csv_data.copy()
    
    if location:
        filtered_data = filtered_data[filtered_data['location'].isin(location)]
    if technology:
        filtered_data = filtered_data[filtered_data['technology'].isin(technology)]
    if duration:
        filtered_data = filtered_data[filtered_data['duration'].isin([int(d) if d.isdigit() else float(d) for d in duration])]
    if power:
        filtered_data = filtered_data[filtered_data['power'].isin([int(p) if p.isdigit() else float(p) for p in power])]
    
    # Generate objective data using the filtered data
    objective_data = generate_objective_graph_data(filtered_data)
    
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