import json
import sys
import os
os.environ['NUMBA_THREADING_LAYER'] = 'omp'
os.environ['NUMBA_NUM_THREADS'] = '1'

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
from plotly.subplots import make_subplots

# Add dashboard directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import specific modules from your dashboard library
from dashlib.offshore_windfarm.vis import Visualizer

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow any origin for development

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

    return {
        "hyperparameters": hyperparameters,
        "input_parameters": input_parameters,
        "objective_functions": objective_functions,
        "decision_variables": decision_variables,
        "csv_data": csv_data
    }

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


def draw_clusters_scatterplot(clusters, points, objective_funcs, selected_indices=None):
    print("Drawing clusters scatterplot...")
    print(points)
    print(objective_funcs)
    fig = go.Figure()

    # Unassigned points
    no_cluster_mask = ~points.index.isin(clusters.index)
    no_cluster_df = points[no_cluster_mask]
    no_cluster_objectives = objective_funcs.loc[no_cluster_df.index]

    # Format hover text for unassigned points
    hover_text = [
        '<br>'.join([f'<b>{col.title()}:</b> {row[col].round(2)}' for col in objective_funcs.columns])
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

    clusters = pd.get_dummies(clusters.iloc[:, 0], dtype=int).replace(0, -1)

    for i, c in enumerate(clusters.columns):
        color_hex = pc.qualitative.D3[i % len(pc.qualitative.D3)]
        color_rgba = rgba_with_opacity(color_hex, 1.0)
        color_fill = rgba_with_opacity(color_hex, 0.15)

        # Group by cluster and get convex hulls
        grouped = points.groupby(clusters[c])
        hulls = [
            get_convex_hull(dfk) for k, dfk in grouped if k != -1
        ]

        # Add convex hull polygons
        for hull in hulls:
            x_coords = hull[0].to_list()
            y_coords = hull[1].to_list()
            fig.add_trace(go.Scatter(
                x=x_coords + [x_coords[0]],
                y=y_coords + [y_coords[0]],
                mode="lines",
                fill="toself",
                fillcolor=color_fill,
                line=dict(color=color_rgba, width=1.5),
                showlegend=False,
                hoverinfo='skip'
            ))

        # Point masks
        mask = clusters[c] != -1
        multi_cluster_mask = (clusters[clusters.columns] != -1).sum(axis=1) > 1
        cluster_points_idx = clusters.index[mask]
        cluster_points = points.loc[cluster_points_idx]
        # Get corresponding objective function values
        cluster_objectives = objective_funcs.loc[cluster_points_idx]

        # Generate hover text dynamically from objective_funcs columns
        hover_text = [
            '<br>'.join([f'<b>{col.title()}:</b> {row[col].round(2)}' for col in objective_funcs.columns])
            for _, row in cluster_objectives.iterrows()
        ]

        # If selection mode is active
        if selected_indices is not None:
            selected_mask = cluster_points.index.isin(selected_indices)

            # Single cluster, unselected
            single_unselected = cluster_points[~multi_cluster_mask & ~selected_mask]
            fig.add_trace(go.Scatter(
                x=single_unselected[0], y=single_unselected[1],
                mode='markers',
                marker=dict(color='lightgray', size=6, opacity=0.6),
                name=f'{c} (unselected)'
            ))

            # Single cluster, selected
            single_selected = cluster_points[~multi_cluster_mask & selected_mask]
            fig.add_trace(go.Scatter(
                x=single_selected[0], y=single_selected[1],
                mode='markers',
                marker=dict(color=color_rgba, size=7),
                name=f'{c} (selected)'
            ))

            # Multi-cluster, unselected
            multi_unselected = cluster_points[multi_cluster_mask & ~selected_mask]
            fig.add_trace(go.Scatter(
                x=multi_unselected[0], y=multi_unselected[1],
                mode='markers',
                marker=dict(color='lightgray', size=6, opacity=0.6),
                name='Multi-cluster (unselected)',
                showlegend=(i == 0)
            ))

            # Multi-cluster, selected
            multi_selected = cluster_points[multi_cluster_mask & selected_mask]
            fig.add_trace(go.Scatter(
                x=multi_selected[0], y=multi_selected[1],
                mode='markers',
                marker=dict(color='black', size=7),
                name='Multi-cluster (selected)',
                showlegend=(i == 0)
            ))

        else:
            # Default view: all clustered points
            cluster_only = cluster_points[~multi_cluster_mask]
            fig.add_trace(go.Scatter(
                x=cluster_only[0], y=cluster_only[1],
                mode='markers',
                marker=dict(color=color_rgba, size=10),
                name=c,
                hoverinfo='text',
                hovertext=hover_text
            ))

            multi_cluster = cluster_points[multi_cluster_mask]
            fig.add_trace(go.Scatter(
                x=multi_cluster[0], y=multi_cluster[1],
                mode='markers',
                marker=dict(color='black', size=10),
                name='Multiple Clusters',
                showlegend=(i == 0)
            ))

    # Improved layout
    fig.update_layout(
        title="",
        margin=dict(t=0, b=10, l=10, r=10),  # t=20 keeps top tight
        legend=dict(
            # title=dict(text='Clusters', font=dict(size=11)),
            orientation="h",
            yanchor="top",
            y=0,
            xanchor="center",
            x=0.5,
            bgcolor='white',
            bordercolor='#d3d3d3',
            borderwidth=1,
            font=dict(size=12),
            itemwidth=30,
            traceorder='normal',
            itemsizing='constant'
        ),
        template="plotly_white",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        shapes=[{
            'type': 'rect',
            'xref': 'paper',   # Relative to full plot area
            'yref': 'paper',
            'x0': 0,           # Start at left
            'y0': 0,           # Start at bottom
            'x1': 1,           # End at right
            'y1': 1,           # End at top
            'line': {
                'color': '#999',     # Border color
                'width': 1.5,        # Border width
                'dash': 'solid'      # Line style
            },
            'fillcolor': 'rgba(255,255,255,0)'  # No fill
        }],
        hovermode='closest',
        showlegend=True,
        height=300,
        width=None,
        autosize=True
    )

    # Improve responsiveness and tooltip behavior
    fig.update_traces(hoverlabel=dict(bgcolor="white", font_size=12))

    return fig

def generate_objective_graph_data(objective_col, data):
    # print("Generating objective graph data...", data)
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

@app.route('/api/files/<filename>', methods=['GET'])
def get_file_data(filename):
    try:
        data = load_case_study_data(filename)
        hyperparams = data["hyperparameters"]
        result = [
            {
                "key": key,
                "name": info.get("name", key),
                "values": info["values"]
            }
            for key, info in hyperparams.items()
            if isinstance(info, dict) and "values" in info and isinstance(info["values"], list)
        ]
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching file data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/scatterplot', methods=['GET'])
def get_scatterplot():
    case_study = request.args.get('use_case')
    if not case_study:
        return jsonify({"error": "Missing query param: use_case"}), 400

    try:
        data = load_case_study_data(case_study)
        hyperparameters = data["hyperparameters"]
        csv_data = data["csv_data"]

        # Safely determine cluster_by
        cluster_by = request.args.get('cluster_by')
        if not cluster_by or cluster_by not in csv_data.columns:
            # Try categorical columns first
            cat_columns = csv_data.select_dtypes(include=['object']).columns.tolist()
            if cat_columns:
                cluster_by = cat_columns[0]
            else:
                # Try numeric columns
                num_columns = csv_data.select_dtypes(include=[np.number]).columns.tolist()
                if num_columns:
                    cluster_by = num_columns[0]
                else:
                    # Last resort: use first column
                    cluster_by = csv_data.columns[0]

        print(f"Clustering by: {cluster_by}")
        
        vis_obj = Visualizer(
            data=csv_data,
            data_ovars=list(data["objective_functions"].keys()),
            data_dvars=list(data["decision_variables"].keys())
        )
        points = vis_obj.joint_xy

        kwargs = dict(
            threshold=0.5,
            clu=HDBSCAN(
                min_cluster_size=2, 
                cluster_selection_epsilon=1., 
                n_jobs=1
            ),
            drop_intermediate=False
        )

        clusters = vis_obj.get_overlapping_clusters(**kwargs)

        # Use cluster_by to determine clustering column
        initial_clusters = csv_data[[cluster_by]]

        query_params = {key: request.args.getlist(key) for key in hyperparameters}
        filtered_data = csv_data.copy()
        
        for key, values in query_params.items():
            if values:
                filtered_data = filtered_data[filtered_data[key].isin(values)]

        updated_clusters = filtered_data[[cluster_by]]
        updated_points = points.loc[filtered_data.index]
        objective_funcs = filtered_data[data["objective_functions"].keys()]

        fig = draw_clusters_scatterplot(updated_clusters, updated_points, objective_funcs)

        return jsonify({
            "scatterplot": fig.to_json(),
            "config": {"displayModeBar": False, "responsive": True},
            "cluster_by": cluster_by
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
        data = load_case_study_data(case_study)
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
        print(weights_input)
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
        data = load_case_study_data(case_study)
        hyperparameters = data["hyperparameters"]
        csv_data = data["csv_data"]

        # Parse filters
        query_params = {key: request.args.getlist(key) for key in hyperparameters}
        filtered_data = csv_data.copy()
        for key, values in query_params.items():
            if values:
                filtered_data = filtered_data[filtered_data[key].isin(values)]

        # Get objective columns
        objective_cols = list(data["objective_functions"].keys())

        # Parse weights
        # Parse weights from individual query parameters
        weights = {}
        for key in request.args:
            if key.startswith("weight_"):
                obj_name = key[len("weight_"):]  # Remove "weight_" prefix
                try:
                    weights[obj_name] = float(request.args[key])
                except ValueError:
                    weights[obj_name] = 1.0  # Default to 1.0 on invalid input

        # Use default weights only for missing objectives
        objective_cols = list(data["objective_functions"].keys())
        for obj in objective_cols:
            if obj not in weights:
                weights[obj] = 1.0

        # Compute weighted score
        filtered_data['weighted_score'] = sum(filtered_data[col] * weights[col] for col in objective_cols)

        # Cluster by parameter passed from frontend
        # Get cluster_by parameter
        cluster_by = request.args.get('cluster_by')

        # Validate that cluster_by exists in the data
        if not cluster_by or cluster_by not in csv_data.columns:
            # Fall back to first categorical column
            cat_columns = csv_data.select_dtypes(include=['object']).columns.tolist()
            if cat_columns:
                cluster_by = cat_columns[0]
            else:
                # Fall back to first numeric column as string category
                num_columns = csv_data.select_dtypes(include=[np.number]).columns.tolist()
                if num_columns:
                    cluster_by = num_columns[0]
                else:
                    cluster_by = csv_data.columns[0]  # Just pick the first one

        # Now safely use cluster_by
        initial_clusters = csv_data[[cluster_by]]

        # Group by cluster and compute stats
        cluster_summary = (
            filtered_data.groupby(cluster_by)
            .agg(
                count=('weighted_score', 'size'),
                avg_weighted_score=('weighted_score', 'mean')
            )
            .reset_index()
            .rename(columns={cluster_by: 'cluster'})
            .sort_values(by='avg_weighted_score', ascending=False)
        )

        return jsonify({
            "clusters": cluster_summary.to_dict(orient='records'),
            "weights_used": weights,
            "cluster_by": cluster_by
        })
    except Exception as e:
        app.logger.error(f"Error fetching weighted solutions: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/decision', methods=['GET'])
def get_decision_plot():
    case_study = request.args.get('use_case')
    if not case_study:
        return jsonify({"error": "Missing query param: use_case"}), 400

    try:
        data = load_case_study_data(case_study)
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
        data = load_case_study_data(case_study)
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
        data = load_case_study_data(case_study)
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
        data = load_case_study_data(case_study)
        hyperparameters = data["hyperparameters"]
        csv_data = data["csv_data"]

        query_params = {key: request.args.getlist(key) for key in hyperparameters}
        filtered_data = csv_data.copy()

        for key, values in query_params.items():
            if values:
                filtered_data = filtered_data[filtered_data[key].isin(values)]

        return jsonify({"data": filtered_data.to_dict(orient='records')})

    except Exception as e:
        app.logger.error(f"Error fetching LMP data: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, threaded=False, host="0.0.0.0", port=8080)