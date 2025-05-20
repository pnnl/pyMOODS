import json
import sys
import os

# Add the dashboard directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

# Import specific modules from your dashboard library
from dashlib.offshore_windfarm.vis import Visualizer

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow any origin for development

MOCODO_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mocodo24_v2_test.json")
with open(MOCODO_JSON_PATH, 'r') as json_file:
    mocodo_data = json.load(json_file)

hyperparameters = mocodo_data["hyperparameters"]
input_parameters = mocodo_data["input_parameters"]
objective_functions = mocodo_data["objective_functions"]
decision_variables = mocodo_data["decision_variables"]
ovars = [list(objective_functions.keys())[0]]
dvars = list(decision_variables.keys())

# Load data for the visualizations
CSV_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "v2_test_summary.csv")
csv_data = pd.read_csv(CSV_FILE_PATH)

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

# from dashlib.offshore_windfarm.screen3 import get_convex_hull
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
        margin=dict(t=20, b=20, l=0, r=0),
        legend=dict(
            x=0.8,
            y=0.95,
            bordercolor='#d3d3d3',
            borderwidth=1,
            bgcolor='white',
            font=dict(
                size=12
            ),
            traceorder='normal',
            title=dict(text=' cluster', font=dict(size=12))
        ),
        template="plotly_white",
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showticklabels=False, showgrid=False)
    )
    return fig

def generate_objective_graph_data(data):
    objective_col = list(objective_functions.keys())[0]
    if not data.empty:
        objective_mean = data[objective_col].mean()
        objective_std = data[objective_col].std()
    else:
        objective_mean = 0
        objective_std = 0

    return {
        "mean": objective_mean,
        "std": objective_std,
        "config": {
            "responsive": True
        }
    }

def generate_stacked_histogram(data):
    size_data = data['size']
    cable_data = data['cable']

    fig = make_subplots(rows=2, cols=1, shared_xaxes=False, vertical_spacing=0.15)

    fig.add_trace(
        go.Histogram(
            x=size_data,
            marker=dict(color='skyblue'),
            name='Size'
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Histogram(
            x=cable_data,
            marker=dict(color='skyblue'),
            name='Cable'
        ),
        row=2, col=1
    )

    fig.update_layout(
        margin=dict(l=5, r=0),
        grid=dict(rows=2, columns=1, pattern='independent'),
        title='Decision Space',
        xaxis=dict(dtick=20),
        yaxis=dict(title='Size', dtick=5, range=[0, 25]),
        xaxis2=dict(dtick=200),
        yaxis2=dict(title='Cable', tickmode='linear', dtick=10, range=[0, 40]),
    )

    return fig

def generate_decision_space_sliders(data):
    objective_col = list(objective_functions.keys())[0]
    data_with_ovar = data.copy()
    data_with_ovar["ovar"] = objective_col
    
    dvars = list(decision_variables.keys())
    fig = distplot_new(data_with_ovar, dvars)
    fig.update_layout(
        # showlegend = False,
        width = 400, height =400,
        margin=dict(l=0,r=190,t=50,b=150),
        autosize= False, font_family='Helvetica',
        font = dict(color='black', size=10), paper_bgcolor='rgba(0,0,0,0)', 
    )
    return fig

def distplot_new(with_clusters, dvars, selected_info=[]):
    y = with_clusters['ovar'].values[0]
    df_with_clusters = pd.melt(with_clusters, id_vars=[y, 'ovar'], value_vars=dvars, var_name='dvar', ignore_index=False)\
        .reset_index()\
        .rename(columns={'index': 'orig_index'}).sort_values([y, 'dvar', 'ovar'])
    ovar = 'objective'
    colors = px.colors.qualitative.D3

    fig = make_subplots(rows=len(dvars), cols=1, shared_xaxes=False, vertical_spacing=0.13)

    for i, dvar in enumerate(dvars):
        row_mask = (df_with_clusters.dvar == dvar)
        if len(selected_info) == 0:
            data = df_with_clusters[row_mask]

            plot = go.Figure()
            plot.add_trace(
                go.Histogram(
                    x=data.value,
                    name=f"{ovar}",
                    marker=dict(color='#2874b4'),
                    nbinsx=100,showlegend=False,
                    hovertemplate='Objective: %{x}<extra></extra>'
                )
            )

            for trace in plot.data:
                trace.showlegend = (i==0)
                fig.add_trace(trace, row=i+1, col=1)
        else:
            if dvar in [d['row'] for d in selected_info]:
                selection = [d for d in selected_info if d['row'] == dvar]
                bounds = [selection[0]['bounds']['x0'], selection[0]['bounds']['x1']]
                data = df_with_clusters[row_mask]
                current = data.sort_values('value').reset_index(drop=True)

                selected_indices = current[current.value.between(bounds[0], bounds[1])].index

                plot = go.Figure()
                plot.add_trace(
                    go.Histogram(
                        x=current.value,
                        name='objective',
                        nbinsx=100,
                        marker=dict(color=colors[0]),
                        selectedpoints=selected_indices,
                        selected=dict(marker=dict(color='#2874b4')),
                        unselected=dict(marker=dict(color='lightgray')),
                        hovertemplate='Objective: %{x}<extra></extra>'
                    )
                )
                for trace in plot.data:
                    trace.showlegend = (i==0)
                    fig.add_trace(trace, row=i+1, col=1)


            # in the other rows
            else:
                filter_query = ''
                for idx in range(len(selected_info)):
                    row = selected_info[idx]['row']
                    curr_bounds = selected_info[idx]['bounds']

                    if idx == 0:
                        filter_query = f"({row} >= {curr_bounds['x0']}) and ({row} <= {curr_bounds['x1']})"
                    else:
                        filter_query += f"and ({row} >= {curr_bounds['x0']}) and ({row} <= {curr_bounds['x1']})"

                filtered = with_clusters.query(filter_query)
                with_clusters['active'] = with_clusters.index.isin(filtered.index)

                df_with_clusters = pd.melt(with_clusters, id_vars=[y, 'ovar', 'active'], value_vars=dvars, var_name='dvar', ignore_index=False)\
                    .reset_index()\
                    .rename(columns={'index': 'orig_index'}).sort_values([y, 'dvar', 'ovar'])

                data = df_with_clusters[row_mask]

                current = data.sort_values('value').reset_index(drop=True)
                plot = go.Figure()
                plot.add_trace(
                    go.Histogram(
                        x=current.value,
                        name='objective',
                        nbinsx=100,
                        marker=dict(color=colors[0]),
                        selectedpoints=current[current.active == True].index, showlegend=False,
                        unselected=dict(marker=dict(color='lightgray'))
                    )
                )

                for trace in plot.data:
                    trace.showlegend = (i==0)
                    fig.add_trace(trace, row=i+1, col=1)


    if len(selected_info) > 0:
        for j in range(len(selected_info)):
            row = selected_info[j]['row']
            bounds = selected_info[j]['bounds']

            fig.add_shape(
                dict(
                    {"type": "rect", "line": {"width": 1, "dash": "dot", "color": "darkgrey"}, 'xref': f'x{dvars.index(row)+1}', 'yref': f'y{dvars.index(row)+1}'},
                    **bounds
                )
            )


    # Add titles as annotations on the left of each subplot
    annotations = [
        dict(
            text=dvar,  # Y-axis title text
            x=10,  # Position relative to the figure (left side)
            y=0.5,  # Centered vertically
            xref="paper",  # Refer to the figure coordinates
            yref="paper",
            showarrow=False,
            textangle=-90,  # Rotate text vertically
            font=dict(size=16)  # Customize font size
        )
    ]

    for i, dvar in enumerate(dvars, start=1):
        annotations.append(
            dict(
                x=1.09,  # Position to the right of the plot area
                y=1.0-(i-0.5)*(1/len(dvars)),  # Center annotation for each subplot
                xref="paper",
                yref="paper",
                text=f"{dvar}",  # Bold text for titles
                showarrow=False,
                xanchor="right",
                yanchor="middle",
                font=dict(size=14),
                textangle=90
            ))
        fig.update_layout({
            f'xaxis{i}': dict(tickfont=dict(size=14)),
            f'yaxis{i}': dict(tickfont=dict(size=14))
        })


    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=10),
        yaxis=dict(tickfont=dict(size=20)),
        legend=dict(
            x=1.09,
            bordercolor='#d3d3d3',
            borderwidth=1,
            bgcolor='white',
            font=dict(
                size=14
            ),

            traceorder='normal',
            title=dict(text=' ovar', font=dict(size=14))
        ),
        barmode="stack",
        annotations=annotations, 
        showlegend =True,
        selectdirection='h', dragmode='select'
    )

    return fig

@app.route('/api/case-studies', methods=['GET'])
def get_case_studies():
    case_study_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo_data")
    print(case_study_dir)
    # Get all .json in the directory
    files = [f for f in os.listdir(case_study_dir) if f.endswith('.json')]
    return jsonify({"files": files})

@app.route('/api/files/<filename>', methods=['GET'])
def get_file_data(filename):
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo_data", filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        hyperparams = data.get("hyperparameters", {})

        # Get keys in the original order
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
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/scatterplot', methods=['GET'])
def get_scatterplot():
    # Get query parameters dynamically based on hyperparameters
    hyperparameter_keys = list(hyperparameters.keys())
    query_params = {key: request.args.getlist(key) for key in hyperparameter_keys}
    
    # Filter data based on parameters if provided
    filtered_data = csv_data.copy()
    
    for key, values in query_params.items():
        if values:
            filtered_data = filtered_data[filtered_data[key].isin(values)]
    
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
    # Get query parameters dynamically based on hyperparameters
    hyperparameter_keys = list(hyperparameters.keys())
    query_params = {key: request.args.getlist(key) for key in hyperparameter_keys}
    
    # Filter data based on parameters if provided
    filtered_data = csv_data.copy()
    
    for key, values in query_params.items():
        if values:
            filtered_data = filtered_data[filtered_data[key].isin(values)]
    
    # Generate mean and std data
    graph_data = generate_objective_graph_data(filtered_data)
    
    # Return the data as JSON
    return jsonify(graph_data)

@app.route('/api/decision', methods=['GET'])
def get_decision_plot():
    hyperparameter_keys = list(hyperparameters.keys())
    query_params = {key: request.args.getlist(key) for key in hyperparameter_keys}

    filtered_data = csv_data.copy()
    for key, values in query_params.items():
        if values:
            filtered_data = filtered_data[filtered_data[key].isin(values)]

    fig = generate_stacked_histogram(filtered_data)
    # fig = generate_decision_space_sliders(filtered_data)

    return jsonify({
        "plot": fig.to_json(),
        "config": {
            "displayModeBar": False,
            "responsive": True,
            "showlegend": False
        }
    })

# potential delete
@app.route('/api/decision_space', methods=['GET'])
def get_decision_space_graph():
    # Get query parameters dynamically based on hyperparameters
    hyperparameter_keys = list(hyperparameters.keys())
    query_params = {key: request.args.getlist(key) for key in hyperparameter_keys}

    # Filter data based on parameters if provided
    filtered_data = csv_data.copy()
    for key, values in query_params.items():
        if values:
            filtered_data = filtered_data[filtered_data[key].isin(values)]

    # Prepare data for the decision space graph
    objective_col = list(objective_functions.keys())[0]
    filtered_data["ovar"] = objective_col
    dvars = list(decision_variables.keys())

    # Generate the decision space graph
    fig = distplot_new(filtered_data, dvars)

    # Return the full figure data as JSON
    return jsonify({
        "plot": fig.to_json(),
        "config": {
            "displayModeBar": False,
            "responsive": True
        }
    })

@app.route('/api/parameters', methods=['GET'])
def get_parameters():
    """
    Returns a dictionary of available filters where keys are hyperparameter names,
    and values are lists of possible options for each hyperparameter.
    """
    parameters = {
        key: info["values"]
        for key, info in hyperparameters.items()
        if "values" in info and isinstance(info["values"], list)
    }
    return jsonify(parameters)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)