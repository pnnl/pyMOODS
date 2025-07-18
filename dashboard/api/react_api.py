import os
os.environ['NUMBA_THREADING_LAYER'] = 'omp'
os.environ['NUMBA_NUM_THREADS'] = '1'
import sys
import json

from collections import OrderedDict
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
import plotly.colors as pc
from scipy.spatial import ConvexHull
from scipy.spatial.qhull import QhullError
from sklearn.cluster import HDBSCAN
from plotly.subplots import make_subplots

import matplotlib.pyplot as plt

# Add dashboard directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import specific modules from your dashboard library
from dashlib.offshore_windfarm.vis import Visualizer

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow any origin for development

# Global cache
USE_CASE_CACHE = {}

# Helper function to load case study data
def load_case_study_data(case_study_name):
    case_study_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo_data")
    json_path = os.path.join(case_study_dir, f"{case_study_name}.json")

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Case study JSON not found: {json_path}")

    with open(json_path, 'r') as f:
        mocodo_data = json.load(f)

    hyperparameters = mocodo_data.get("hyperparameters", {})
    input_parameters = mocodo_data.get("input_parameters", {})
    objective_functions = mocodo_data.get("objective_functions", {})
    decision_variables = mocodo_data.get("decision_variables", {})

    # Load corresponding CSV
    csv_file_name = mocodo_data.get("datafile", None)
    if not csv_file_name:
        raise ValueError(f"'datafile' not defined in {case_study_name}.json")

    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo_data", csv_file_name)
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    csv_data = pd.read_csv(csv_path)
    csv_data.index.set_names('Solution ID', inplace=True)
    csv_data.index = csv_data.index.astype(int)
    csv_data.reset_index(inplace=True)

    # Load corresponding Scenarios
    scenario_filename = mocodo_data.get("scenariofile", None)
    if scenario_filename:
        scenariofile_path = os.path.join(
        os.path.dirname(
            os.path.dirname(__file__)
        ), 
        "demo_data", 
        scenario_filename
    )
        if not os.path.exists(scenariofile_path):
            raise FileNotFoundError(f"Scenario file not found: {scenariofile_path}")
        scenario_data = pd.read_csv(scenariofile_path)
    
    else:
        scenario_data = None
    # if not scenario_filename:
    #     raise ValueError(f"'scenariofile' not defined in {case_study_name}.json")

    
    

    # scenario_data = pd.read_csv(scenariofile_path)

    result = {
        "hyperparameters": hyperparameters,
        "input_parameters": input_parameters,
        "objective_functions": objective_functions,
        "decision_variables": decision_variables,
        "csv_data": csv_data,
        "scenario_data": scenario_data
    }

    USE_CASE_CACHE[case_study_name] = result

    return result

# Plotting Functions
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

def rgba_with_opacity(rgb_hex, opacity=1.0):
    """Convert hex color to rgba string with opacity"""
    rgb = pc.hex_to_rgb(rgb_hex)
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity})"


def draw_clusters_scatterplot(
    full_dataset,
    points, 
    clusters, 
    objective_keys,
    color_by=None,     
    size=None          
):
    fig = go.Figure()
    objective_funcs = full_dataset[objective_keys]
    
    # Unassigned points
    no_cluster_mask = ~points.index.isin(clusters.index)
    no_cluster_df = points[no_cluster_mask]
    no_cluster_objectives = objective_funcs.loc[no_cluster_df.index]
    hover_text = [
        '<br>'.join([f'<b>{col.title()}:</b> {row[col]}' for col in objective_funcs.columns])
        for _, row in no_cluster_objectives.iterrows()
    ]
    fig.add_trace(go.Scatter(
        x=no_cluster_df[0], y=no_cluster_df[1],
        mode='markers',
        marker=dict(color='lightgray', size=4, opacity=0.3),
        name='Unassigned',
        hoverinfo='text',
        hovertext=hover_text
    ))

    # Clustering and coloring logic
    clustering = pd.get_dummies(clusters.iloc[:, 0], dtype=int).replace(0, -1)
    use_coloring = color_by in full_dataset.columns
    if use_coloring:
        color_vals = full_dataset[color_by].dropna().unique()
        color_palette = pc.qualitative.D3
        color_map = {val: rgba_with_opacity(color_palette[i % len(color_palette)], 1.0)
                     for i, val in enumerate(color_vals)}

    # Keep track of which color_by values have already appeared in the legend
    seen_legend = set()
    
    for i, c in enumerate(clustering.columns):
        mask = clustering[c] != -1
        cluster_points_idx = clustering.index[mask]
        cluster_points = points.loc[cluster_points_idx]
        cluster_objectives = full_dataset.loc[cluster_points_idx]
        generalizer_mask = (clustering[clustering.columns] != -1).sum(axis=1) > 1

        if size is not None and isinstance(size, pd.Series):
            point_sizes = size.loc[cluster_points_idx]
            diff = point_sizes.max() - point_sizes.min()
            if abs(diff) < 1: diff = 1  # Avoid division by zero
            point_sizes = (point_sizes - point_sizes.min()) / diff
            point_sizes = point_sizes * 30 + 5
        else:
            point_sizes = pd.Series(10, index=cluster_points_idx)

        if use_coloring:
            cluster_colors = full_dataset.loc[cluster_points_idx, color_by]
            for val in cluster_colors.unique():
                idx = cluster_colors[cluster_colors == val].index
                subset_points = cluster_points.loc[idx]
                subset_objectives = cluster_objectives.loc[idx]
                hover_text = [
                    '<br>'.join([f'<b>{col.title()}:</b> {row[col]}' for col in objective_funcs.columns])
                    for _, row in subset_objectives.iterrows()
                ]
                fig.add_trace(go.Scatter(
                    x=subset_points[0], y=subset_points[1],
                    mode='markers',
                    marker=dict(color=color_map[val], size=point_sizes.loc[idx]),
                    name=str(val),
                    legendgroup=str(val),
                    hoverinfo='text',
                    hovertext=hover_text,
                    showlegend=(val not in seen_legend)
                ))
                seen_legend.add(val)
        else:
            hover_text = [
                '<br>'.join([f'<b>{col.title()}:</b> {row[col]}' for col in objective_funcs.columns])
                for _, row in cluster_objectives.iterrows()
            ]
            fig.add_trace(go.Scatter(
                x=cluster_points[0], y=cluster_points[1],
                mode='markers',
                marker=dict(color=pc.qualitative.D3[i % len(pc.qualitative.D3)], size=point_sizes),
                name=c,
                hoverinfo='text',
                hovertext=hover_text
            ))

        generalizers = cluster_points[generalizer_mask]
        if not generalizers.empty:
            fig.add_trace(go.Scatter(
                x=generalizers[0], y=generalizers[1],
                mode='markers',
                marker=dict(color='black', size=point_sizes.loc[generalizers.index]),
                name='Generalizers',
                showlegend=(i == 0)
            ))

    fig.update_layout(
        title="",
        margin=dict(t=0, b=10, l=10, r=10),
        legend=dict(
            orientation="h", yanchor="top", y=0, xanchor="center", x=0.5,
            bgcolor='white', bordercolor='#d3d3d3', borderwidth=1,
            font=dict(size=10), itemwidth=30, traceorder='normal', itemsizing='constant'
        ),
        template="plotly_white",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        shapes=[{
            'type': 'rect',
            'xref': 'paper', 'yref': 'paper',
            'x0': 0, 'y0': 0, 'x1': 1, 'y1': 1,
            'line': {'color': '#999', 'width': 1.5, 'dash': 'solid'},
            'fillcolor': 'rgba(255,255,255,0)'
        }],
        hovermode='closest',
        showlegend=True,
        height=300,
        autosize=True
    )
    fig.update_traces(hoverlabel=dict(bgcolor="white", font_size=12))
    
    x_min, x_max = points[0].min(), points[0].max()
    y_min, y_max = points[1].min(), points[1].max()

    # Add a 15% buffer on each side
    x_buffer = 0.15 * (x_max - x_min)
    y_buffer = 0.15 * (y_max - y_min)

    xrange = [x_min - x_buffer, x_max + x_buffer]
    yrange = [y_min - y_buffer, y_max + y_buffer]

    fig.update_layout(
        xaxis=dict(range=xrange, autorange=False),
        yaxis=dict(range=yrange, autorange=False)
    )

    return fig

def generate_objective_graph_data(objective_col, data):
    # objective_col = list(data["objective_functions"].keys())[0]
    objective_mean = data[objective_col].mean() if not data.empty else 0
    objective_std = data[objective_col].std() if not data.empty else 0
    return {
        "mean": objective_mean,
        "std": objective_std,
        "config": {"responsive": True}
    }

def generate_stacked_histogram(filtered_data):
    size_data = filtered_data['size']
    cable_data = filtered_data['cable']
    fig = make_subplots(rows=2, cols=1, shared_xaxes=False, vertical_spacing=0.15)
    fig.add_trace(go.Histogram(x=size_data, marker=dict(color='skyblue'), name='Size'), row=1, col=1)
    fig.add_trace(go.Histogram(x=cable_data, marker=dict(color='skyblue'), name='Cable'), row=2, col=1)
    fig.update_layout(
        margin=dict(l=5, r=0),
        grid=dict(rows=2, columns=1, pattern='independent'),
        title='Decision Space',
        xaxis=dict(dtick=20), yaxis=dict(title='Size', dtick=5, range=[0, 25]),
        xaxis2=dict(dtick=200), yaxis2=dict(title='Cable', tickmode='linear', dtick=10, range=[0, 40]),
    )
    return fig

def distplot_new(with_clusters, dvars, selected_info=[]):
    y = with_clusters['ovar'].iloc[0]
    df_with_clusters = pd.melt(with_clusters, id_vars=[y, 'ovar'], value_vars=dvars,
                               var_name='dvar', ignore_index=False).reset_index() \
        .rename(columns={'index': 'orig_index'}).sort_values([y, 'dvar', 'ovar'])

    ovar = 'objective'
    colors = px.colors.qualitative.D3

    fig = make_subplots(rows=len(dvars), cols=1, shared_xaxes=False, vertical_spacing=0.13)

    for i, dvar in enumerate(dvars):
        row_mask = (df_with_clusters.dvar == dvar)
        if len(selected_info) == 0:
            data = df_with_clusters[row_mask]
            plot = go.Figure()
            plot.add_trace(go.Histogram(
                x=data.value,
                name=f"{ovar}",
                marker=dict(color='#2874b4'),
                nbinsx=100,
                showlegend=False,
                hovertemplate='Objective: %{x}<extra></extra>'
            ))
            for trace in plot.data:
                trace.showlegend = (i == 0)
                fig.add_trace(trace, row=i + 1, col=1)
        else:
            if dvar in [d['row'] for d in selected_info]:
                selection = [d for d in selected_info if d['row'] == dvar]
                bounds = [selection[0]['bounds']['x0'], selection[0]['bounds']['x1']]
                current = df_with_clusters[row_mask].sort_values('value').reset_index(drop=True)
                selected_indices = current[current.value.between(bounds[0], bounds[1])].index
                plot = go.Figure()
                plot.add_trace(go.Histogram(
                    x=current.value,
                    name='objective',
                    nbinsx=100,
                    marker=dict(color=colors[0]),
                    selectedpoints=selected_indices,
                    selected=dict(marker=dict(color='#2874b4')),
                    unselected=dict(marker=dict(color='lightgray')),
                    hovertemplate='Objective: %{x}<extra></extra>'
                ))
                for trace in plot.data:
                    trace.showlegend = (i == 0)
                    fig.add_trace(trace, row=i + 1, col=1)
            else:
                filter_query = ''
                for idx, info in enumerate(selected_info):
                    row = info['row']
                    curr_bounds = info['bounds']
                    if idx == 0:
                        filter_query = f"({row} >= {curr_bounds['x0']}) and ({row} <= {curr_bounds['x1']})"
                    else:
                        filter_query += f" and ({row} >= {curr_bounds['x0']}) and ({row} <= {curr_bounds['x1']})"
                filtered = with_clusters.query(filter_query)
                with_clusters['active'] = with_clusters.index.isin(filtered.index)
                df_with_clusters = pd.melt(with_clusters, id_vars=[y, 'ovar', 'active'],
                                          value_vars=dvars, var_name='dvar', ignore_index=False) \
                    .reset_index().rename(columns={'index': 'orig_index'}) \
                    .sort_values([y, 'dvar', 'ovar'])
                data = df_with_clusters[df_with_clusters.dvar == dvar]
                current = data.sort_values('value').reset_index(drop=True)
                plot = go.Figure()
                plot.add_trace(go.Histogram(
                    x=current.value,
                    name='objective',
                    nbinsx=100,
                    marker=dict(color=colors[0]),
                    selectedpoints=current[current.active == True].index,
                    unselected=dict(marker=dict(color='lightgray'))
                ))
                for trace in plot.data:
                    trace.showlegend = (i == 0)
                    fig.add_trace(trace, row=i + 1, col=1)

    if len(selected_info) > 0:
        for j, info in enumerate(selected_info):
            row = info['row']
            bounds = info['bounds']
            fig.add_shape(dict(
                type="rect", line={"width": 1, "dash": "dot", "color": "darkgrey"},
                xref=f"x{dvars.index(row)+1}", yref=f"y{dvars.index(row)+1}", **bounds
            ))

    annotations = []
    for i, dvar in enumerate(dvars, start=1):
        annotations.append(dict(
            x=1.09, y=1.0 - (i - 0.5) * (1 / len(dvars)),
            xref="paper", yref="paper",
            text=f"{dvar}", showarrow=False, xanchor="right", yanchor="middle",
            font=dict(size=14), textangle=90
        ))

    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=10),
        yaxis=dict(tickfont=dict(size=20)),
        legend=dict(x=1.09, bordercolor='#d3d3d3', borderwidth=1, bgcolor='white',
                    font=dict(size=14), traceorder='normal', title=dict(text=' ovar', font=dict(size=14))),
        barmode="stack", annotations=annotations, showlegend=True, selectdirection='h', dragmode='select'
    )
    return fig

# API Routes
@app.route('/api/case-studies', methods=['GET'])
def get_case_studies():
    case_study_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo_data")
    files = [f.split(".")[0] for f in os.listdir(case_study_dir) if f.endswith('.json')]
    return jsonify({"files": files})

@app.route('/api/init', methods=['GET'])
def get_init_data():
    use_case = request.args.get('use_case')
    if not use_case:
        return jsonify({"error": "Missing query param: use_case"}), 400
    try:
        data = load_case_study_data(use_case)

        # Parameters for filters
        hyperparams = data["hyperparameters"]
        filter_options = [
            {
                "key": key,
                "name": info.get("name", key),
                "values": info["values"],
                "is_clusterable": True
            }
            for key, info in hyperparams.items()
            if isinstance(info, dict) and "values" in info and isinstance(info["values"], list)
        ]

        # Objective weights
        objective_cols = list(data["objective_functions"].keys())
        default_weights = {col: 1 for col in objective_cols}

        return jsonify({
            "filters": filter_options,
            "objectives": default_weights
        })

    except Exception as e:
        app.logger.error(f"Error initializing data: {str(e)}")
        return jsonify({"error": str(e)}), 500

# @app.route('/api/files/<filename>', methods=['GET'])
# def get_file_data(filename):
#     try:
#         data = load_case_study_data(filename)
#         hyperparams = data["hyperparameters"]
#         result = [
#             {
#                 "key": key,
#                 "name": info.get("name", key),
#                 "values": info["values"]
#             }
#             for key, info in hyperparams.items()
#             if isinstance(info, dict) and "values" in info and isinstance(info["values"], list)
#         ]
#         return jsonify(result)
#     except Exception as e:
#         app.logger.error(f"Error fetching file data: {str(e)}")
#         return jsonify({"error": str(e)}), 500

@app.route('/api/project', methods=['POST'])
def get_projection_data():
    """Receive solution IDs and color_by field, return 2D projection"""
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "No JSON payload received"}), 400

        # Get required fields
        use_case = payload.get('use_case')
        if not use_case:
            return jsonify({"error": "Missing query param: use_case"}), 400

        solution_ids = payload.get("solution_ids")
        color_by = payload.get("color_by", None)
        
        if not solution_ids:
            return jsonify({"error": "Missing 'solution_ids' in request"}), 400

        # Get data from cache
        if use_case not in USE_CASE_CACHE:
            return jsonify({"error": f"Unknown use_case: {use_case}"}), 400

        # Filter dataset to selected solutions
        filtered_data = pd.DataFrame(solution_ids)
        
        # Extract objective functions
        objective_keys = list(USE_CASE_CACHE[use_case]["objective_functions"].keys())
        decision_keys = list(USE_CASE_CACHE[use_case]["decision_variables"].keys())
        
        # Initialize Visualizer
        vis_obj = Visualizer(
            data=filtered_data,
            data_ovars=objective_keys,
            data_dvars=decision_keys
        )
        
        # Get joint XY coordinates
        points = vis_obj.joint_xy
        updated_points = points.loc[filtered_data.index]
        updated_points.columns = ["x_coord", "y_coord"]

        # Get clusters for filtered data
        clusters = vis_obj.df_clustered.loc[filtered_data.index, ["label"]]
        print("Data:::::", updated_points, clusters, filtered_data)
        pd.concat([updated_points, clusters, filtered_data], axis=1).to_csv("test.csv")
        
        # Prepare response
        result = {
            "x": updated_points[0].tolist(),
            "y": updated_points[1].tolist()
        }

        # Optional color values
        if color_by and color_by in filtered_data.columns:
            result["colorValues"] = filtered_data[color_by].fillna("Unknown").tolist()

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Error generating projections: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/scatterplot', methods=['GET'])
def get_scatterplot():
    """Get scatterplot data with optimized filtering and parameter handling"""
    case_study = request.args.get('use_case')
    if not case_study:
        return jsonify({"error": "Missing query param: use_case"}), 400

    try:
        # Load case study data
        data = USE_CASE_CACHE[case_study]
        hyperparameters = data["hyperparameters"]
        csv_data = data["csv_data"]

        # Get color_by parameter
        color_by = request.args.get('color_by')

        # Initialize Visualizer
        vis_obj = Visualizer(
            data=csv_data,
            data_ovars=list(data["objective_functions"].keys()),
            data_dvars=list(data["decision_variables"].keys())
        )
        points = vis_obj.joint_xy

        # Apply filters
        query_params = {key: request.args.getlist(key) for key in hyperparameters}
        filtered_data = csv_data.copy()
        
        # Efficient filtering using vectorized operations
        for key, values in query_params.items():
            if values:
                filtered_data = filtered_data[filtered_data[key].isin(values)]

        # Get clusters for filtered data
        clusters = vis_obj.df_clustered.loc[filtered_data.index, ["label"]]
        
        # Extract relevant points for filtered data
        updated_points = points.loc[filtered_data.index]
        
        # Extract objective functions
        objective_keys = list(data["objective_functions"].keys())
        objective_funcs = filtered_data[objective_keys]

        # Size encoding based on weights
        weights_input = request.args.get('weights')
        weights = {}
        if weights_input:
            try:
                weights = json.loads(weights_input)
                weights = {
                    k: float(v) for k, v in weights.items() 
                    if k in objective_funcs.columns
                }
            except Exception as e:
                app.logger.warning(f"Invalid weights JSON: {str(e)}")

        if weights:
            size = objective_funcs[list(weights.keys())].mul(list(weights.values())).sum(axis=1)
        else:
            size = 10
            
        # print("Computed sizes:", size)
        # Normalize and scale marker sizes
        # size = size.abs().clip(lower=5, upper=55)

        # Generate the figure
        fig = draw_clusters_scatterplot(
            full_dataset=filtered_data,
            points=updated_points,
            clusters=clusters,
            objective_keys=objective_keys,
            color_by=color_by,
            size=size
        )

        return jsonify({
            "scatterplot": fig.to_json(),
            "config": {"displayModeBar": False, "responsive": True},
            "color_by": color_by
        })

    except Exception as e:
        app.logger.error(f"Error generating scatterplot: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/objective', methods=['GET'])
def get_objective_data():
    case_study = request.args.get('use_case')
    if not case_study:
        return jsonify({"error": "Missing query param: use_case"}), 400
    try:
        data = USE_CASE_CACHE[case_study]
        hyperparameters = data["hyperparameters"]
        csv_data = data["csv_data"]
        
        # Get all objective columns
        objective_cols = list(data["objective_functions"].keys())
        
        # Parse filters
        query_params = {key: request.args.getlist(key) for key in hyperparameters}
        filtered_data = csv_data.copy()
        for key, values in query_params.items():
            if values:
                filtered_data = filtered_data[filtered_data[key].isin(values)]

        # Parse weights
        weights_input = request.args.get('weights')
        if weights_input:
            weights = json.loads(weights_input)
        else:
            # Default equal weights
            weights = {col: 1 / len(objective_cols) for col in objective_cols}

        # Calculate weighted average
        weighted_score = sum(filtered_data[col] * weights[col] for col in objective_cols).mean()

        return jsonify({
            "mean_weighted_score": weighted_score,
            "weights_used": weights,
            "config": {"responsive": True}
        })
    except Exception as e:
        app.logger.error(f"Error generating objective data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/solutions', methods=['GET'])
def get_weighted_solutions():
    case_study = request.args.get('use_case')
    if not case_study:
        return jsonify({"error": "Missing query param: use_case"}), 400
    try:
        data = USE_CASE_CACHE[case_study]
        
        # read hyperparameters and csv_data from the cached data
        hyperparameters = data["hyperparameters"]
        csv_data = data["csv_data"]
        
        # apply filters
        query_params = {key: request.args.getlist(key) for key in hyperparameters}
        filtered_data = csv_data.copy()
        for key, values in query_params.items():
            if values:
                filtered_data = filtered_data[filtered_data[key].isin(values)]
        
        # Get objective columns
        ovars = list(data["objective_functions"].keys())
        dvars = list(data["decision_variables"].keys())

        # Initialize Visualizer
        vis_obj = Visualizer(
            data=csv_data,
            data_ovars=ovars,
            data_dvars=dvars
        )
        
        # get projections and clusters for filtered data indices
        points = vis_obj.joint_xy.loc[filtered_data.index]
        # get clusters for filtered data
        clusters = vis_obj.df_clustered.loc[filtered_data.index, ["label"]]
        
        # merge projections and clusters with filtered data
        filtered_data = pd.concat([filtered_data, points, clusters], axis=1)
        filtered_data = filtered_data.rename(columns={0: 'x_coord', 1: 'y_coord'})
        print("Duplicate Solution IDs - backend",filtered_data['Solution ID'].value_counts()[filtered_data['Solution ID'].value_counts() > 1])

        
        # parse weights from query params
        weights = {}
        for key in request.args:
            if key.startswith("weight_"):
                obj_name = key[len("weight_"):]
                try:
                    weights[obj_name] = float(request.args[key])
                except ValueError:
                    weights[obj_name] = 1.0
        
        # Default weights for missing objectives
        for obj in ovars:
            if obj not in weights:
                weights[obj] = 1.0

        # Compute weighted score
        filtered_data['Weighted Sum'] = sum(filtered_data[col] * weights[col] for col in ovars)

        # Sort by weighted score descending and take top 5
        # top_solutions = filtered_data.sort_values(by='Weighted Sum', ascending=False)
        # print(top_solutions.iloc[0])
        #     list(hyperparameters.keys()) + decision_cols + ['Weighted Sum']
        # ]

        # Scale the objective columns for ranking
        # scale = {
        #     'Cable Material Cost($M)': -1,
        #     'Battery Cost($M)': -1,
        #     'Day-Ahead Revenue ($k)': 1,
        #     'Real-Time Revenue ($k)': 1,
        #     'Reserve WF Revenue ($k)': 1,
        #     'Reserve ESS Revenue ($k)': 1
        # }
        # scale_series = pd.Series(scale)
        # rank_frame = filtered_data.head(5).copy()
        # print(rank_frame)
        # rank_frame.index = (rank_frame["Case Study"] + "," + rank_frame["Location"])
        # rank_frame = rank_frame[ovars]
        
        # Apply scaling and rank
        # rank_frame = rank_frame * scale_series
        # rank_frame = rank_frame.rank(ascending=False)
        # print(rank_frame.to_dict(orient='index'))
        
        # Convert to dict for JSON response
        solution_dict = [
            OrderedDict([(col, row[col]) for col in filtered_data.columns])
            for _, row in filtered_data.iterrows()
        ]
        
        return Response(
            json.dumps({
                "solutions": solution_dict,
                "ranks": filtered_data[ovars].to_dict(orient='index'),
                "weights_used": weights,
                "index_keys": ['Solution ID'],
                "objective_keys": ovars,
                "decision_keys": dvars,
                "hyperparameter_keys": list(hyperparameters.keys()),
                "additional_cols": ['Weighted Sum']
            }, sort_keys=False),
            mimetype='application/json'
        )

    except Exception as e:
        app.logger.error(f"Error fetching weighted solutions: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/objective-plot-data', methods=['GET'])
def get_objective_plot_data():
    case_study = request.args.get('use_case')
    if not case_study:
        return jsonify({"error": "Missing query param: use_case"}), 400

    try:
        data = USE_CASE_CACHE[case_study]
        hyperparameters = data["hyperparameters"]
        csv_data = data["csv_data"]

        # Parse filters from query params
        query_params = {key: request.args.getlist(key) for key in hyperparameters}

        # Apply filters
        filtered_data = csv_data.copy()
        if any(query_params[key] for key in query_params):
            for key, values in query_params.items():
                if values:
                    filtered_data = filtered_data[filtered_data[key].isin(values)]
        else:
            print("No filters applied, returning full dataset")

        # Objective Functions
        objective_cols = list(data["objective_functions"].keys())
        
        # Parse weights from query params
        weights = {}
        for key in request.args:
            if key.startswith("weight_"):
                obj_name = key[len("weight_"):]
                try:
                    weights[obj_name] = float(request.args[key])
                except ValueError:
                    weights[obj_name] = 1.0
        
        # Default weights for missing objectives
        for obj in objective_cols:
            if obj not in weights:
                weights[obj] = 1.0

        # Compute weighted score
        filtered_data['Weighted Sum'] = sum(filtered_data[col] * weights[col] for col in objective_cols)

        # Sort by weighted score descending and take top 5
        filtered_data = filtered_data.sort_values(by='Weighted Sum', ascending=False)
        
        objectives = []
        for col in objective_cols:
            distribution = filtered_data[col].tolist()
            selected_value = filtered_data.iloc[0][col]
            max_value = max(distribution) if distribution else 1
            objectives.append({
                "variable": col,
                "distribution": distribution,
                "selected": selected_value,
                "max": max_value
            })
        
        # Decision Variables (assumed to be in hyperparameters or as columns in CSV)
        decision_cols = list(data["decision_variables"].keys())  # Or define a separate list
        
        decisions = []
        for col in decision_cols:
            distribution = filtered_data[col].tolist()
            selected_value = filtered_data.iloc[0][col]
            max_value = max(distribution) if distribution else 1
            decisions.append({
                "variable": col,
                "distribution": distribution,
                "selected": selected_value,
                "max": max_value
            })

        # Return both objectives and decisions
        return jsonify({
            "objectives": objectives,
            "decisions": decisions
        })

    except Exception as e:
        app.logger.error(f"Error fetching objective plot data: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/decision', methods=['GET'])
def get_decision_plot():
    case_study = request.args.get('use_case')
    if not case_study:
        return jsonify({"error": "Missing query param: use_case"}), 400

    try:
        data = USE_CASE_CACHE[case_study]
        hyperparameters = data["hyperparameters"]
        csv_data = data["csv_data"]

        query_params = {key: request.args.getlist(key) for key in hyperparameters}
        filtered_data = csv_data.copy()

        for key, values in query_params.items():
            if values:
                filtered_data = filtered_data[filtered_data[key].isin(values)]

        fig = generate_stacked_histogram(filtered_data)
        return jsonify({
            "plot": fig.to_json(),
            "config": {"displayModeBar": False, "responsive": True, "showlegend": False}
        })

    except Exception as e:
        app.logger.error(f"Error generating decision plot: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/decision_space', methods=['GET'])
def get_decision_space_graph():
    case_study = request.args.get('use_case')
    if not case_study:
        return jsonify({"error": "Missing query param: use_case"}), 400

    try:
        data = USE_CASE_CACHE[case_study]
        hyperparameters = data["hyperparameters"]
        csv_data = data["csv_data"]
        objective_col = list(data["objective_functions"].keys())[0]
        dvars = list(data["decision_variables"].keys())
        filtered_data = csv_data.copy()

        query_params = {key: request.args.getlist(key) for key in hyperparameters}
        for key, values in query_params.items():
            if values:
                filtered_data = filtered_data[filtered_data[key].isin(values)]

        filtered_data["ovar"] = objective_col
        fig = distplot_new(filtered_data, dvars)
        return jsonify({
            "plot": fig.to_json(),
            "config": {"displayModeBar": False, "responsive": True}
        })

    except Exception as e:
        app.logger.error(f"Error generating decision space graph: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/parameters', methods=['GET'])
def get_parameters():
    case_study = request.args.get('use_case')
    if not case_study:
        return jsonify({"error": "Missing query param: use_case"}), 400
    try:
        data = USE_CASE_CACHE[case_study]
        hyperparams = data["hyperparameters"]
        result = [
            {
                "key": key,
                "name": info.get("name", key),
                "values": info["values"],
                "is_clusterable": True  # You can add logic here if needed
            }
            for key, info in hyperparams.items()
            if isinstance(info, dict) and "values" in info and isinstance(info["values"], list)
        ]
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching parameters: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/lmp', methods=['GET'])
def get_lmp_data():
    case_study = request.args.get('use_case')
    if not case_study:
        return jsonify({"error": "Missing query param: use_case"}), 400

    try:
        data = USE_CASE_CACHE[case_study]
        hyperparameters = data["hyperparameters"]
        scenario_data = data.get("scenario_data", None)
        if scenario_data is None:
            return jsonify({"data": []})
        print(scenario_data)

        query_params = {key: request.args.getlist(key) for key in hyperparameters}
        filtered_data = scenario_data.copy()

        for key, values in query_params.items():
            if values:
                filtered_data = filtered_data[filtered_data[key].isin(values)]

        return jsonify({"data": filtered_data.to_dict(orient='records')})

    except Exception as e:
        app.logger.error(f"Error fetching LMP data: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, threaded=False, host="0.0.0.0", port=8080)