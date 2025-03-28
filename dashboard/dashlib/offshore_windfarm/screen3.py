external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
import json, os, sys
import pandas as pd
import plotly.express as px
import numpy as np
from dash import Dash, dcc, html, Input, Output
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.colors as pc
from sklearn.cluster import HDBSCAN, DBSCAN
from scipy.spatial import ConvexHull
from scipy.spatial.qhull import QhullError

from plotly.subplots import make_subplots


sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from offshore_windfarm import vis


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Paths to the data files
MOCODO_JSON_PATH = os.path.join(BASE_DIR, "../../data/mocodo24_v2_test.json")
CSV_FILE_PATH = os.path.join(BASE_DIR, "../../data/v2_test_summary.csv")
LMP_CSV_PATH = os.path.join(BASE_DIR, "../../data/LMP.csv")
DATA_DIR = os.path.join(BASE_DIR, "../../data")
LOCATIONS_FILES = {
    "COTTONWOOD": os.path.join(DATA_DIR, "COTTONWOOD_2018.csv"),
    "JOHNDAY": os.path.join(DATA_DIR, "JOHNDAY_2018.csv"),
    "MOSSLAND": os.path.join(DATA_DIR, "MOSSLAND_2018.csv"),
    "TESLA": os.path.join(DATA_DIR, "TESLA_2018.csv"),
    "WCASCADE": os.path.join(DATA_DIR, "WCASCADE_2018.csv"),
}

# Load and parse mocodo.json
with open(MOCODO_JSON_PATH, 'r') as file:
    mocodo_data = json.load(file)

hyperparameters = mocodo_data["hyperparameters"]
input_parameters = mocodo_data["input_parameters"]
objective_functions = mocodo_data["objective_functions"]
decision_variables = mocodo_data["decision_variables"]


def load_csv_data(file_path):
    return pd.read_csv(CSV_FILE_PATH)


# Convert CSV to DataFrame
csv_data = pd.read_csv(CSV_FILE_PATH)

# Convert CSV to JSON
csv_data_json = csv_data.to_dict(orient="records")

ovars = [list(objective_functions.keys())[0]]
dvars = list(decision_variables.keys())

vis_obj = vis.Visualizer(data=csv_data, data_ovars=ovars, data_dvars=dvars)

points = vis_obj.joint_xy

kwargs = dict(
        threshold=0.5,
        clu = HDBSCAN(
            cluster_selection_epsilon=1.,
            min_cluster_size=10
        ),
        drop_intermediate=False
    )

clusters = vis_obj.get_overlapping_clusters(**kwargs)

initial_clusters = csv_data[['location']]
def blank_figure():
    fig = go.Figure(go.Line(x=[], y=[]))
    fig.update_layout(template=None)
    fig.update_xaxes(showgrid=False,
                     showticklabels=False,
                     zeroline=False,
                     title_standoff=5)
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False)

    return fig

# Generate Dropdown Options for Hyperparameters
def get_hyperparameter_dropdown():
    dropdowns = []
    for key, param in hyperparameters.items():
        if key != "other_cols":  # Skip 'other_cols'
            default_value = param.get('values', [])[0] if param.get(
                'values', []) else None
            dropdown = dcc.Dropdown(
                id={
                    "type": "hyperparameter-dropdown",
                    "key": key
                },
                options=[{
                    'label': str(value),
                    'value': value
                } for value in param.get('values', [])],
                value=None,
                multi=True,  # Multi-value selection
                placeholder=f'Select {param["name"]}...',
                style={
                    'width': '90%',
                    'height': '20%',
                    'maxHeight': '150px',
                    'margin': '5px 0',
                })
            dropdowns.append(
                html.Div(
                    [
                        html.Label(param["name"], style={'fontSize': '15px'}),
                        dropdown
                    ],
                    style={
                        'width': '100%',
                        'height': '59%'
                    }))
    return dropdowns


def get_location_dropdown():
    return dcc.Dropdown(
        id="location-dropdown",
        options=[{
            'label': loc,
            'value': loc
        } for loc in input_parameters["location"]["values"]],
        value=[],multi=True,
        placeholder='Select Location...',
        style={
            'width': '90%',
            'height': '20%',
            'maxHeight': '150px',
            'margin': '5px 0'
        })


Data_folder = "/data"

def generate_time_series(location):
    # If multiple locations are selected, iterate and add each trace. 
    if isinstance(location, list): 
        if not location: 
            return blank_figure() 
        fig = go.Figure() 
        for loc in location: # Only add the trace if the location key exists. 
            if loc in LOCATIONS_FILES: 
                file_path = LOCATIONS_FILES[loc] 
                data = pd.read_csv(file_path, header=1) 
                hourly_windSpeed = data.groupby('Hour')['wind speed at 100m (m/s)'].mean().reset_index() 
                fig.add_trace(go.Scatter( x=hourly_windSpeed["Hour"], y=hourly_windSpeed["wind speed at 100m (m/s)"], mode='lines', name=loc )) 
                fig.update_layout( title=f"Wind Speed TimeSeries for {', '.join(location)}", xaxis_title="Hour", yaxis_title="Wind Speed (m/s)", dragmode='select', selectdirection='h', paper_bgcolor='rgb(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', template='simple_white' ) 
                fig.update_xaxes(rangeslider_visible=True, rangeslider_thickness=0.2) 
                return fig 
            else: # Process single location. 
                if location not in LOCATIONS_FILES: 
                    return blank_figure() 
                file_path = LOCATIONS_FILES[location] 
                data = pd.read_csv(file_path, header=1) 
                hourly_windSpeed = data.groupby('Hour')['wind speed at 100m (m/s)'].mean().reset_index() 
                fig = px.line(hourly_windSpeed, x="Hour", y="wind speed at 100m (m/s)", title=f"Wind Speed TimeSeries for {location}") 
                fig.update_layout( xaxis_title="Hour", yaxis_title="Wind Speed (m/s)", dragmode='select', selectdirection='h', paper_bgcolor='rgb(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', template='simple_white' ) 
                fig.update_xaxes(rangeslider_visible=True, rangeslider_thickness=0.2) 
                return fig

def generate_fairness_index():
    if not os.path.exists(LMP_CSV_PATH):
        return blank_figure()
    data = pd.read_csv(LMP_CSV_PATH)
    if data.empty:
        return blank_figure()
    data["INTERVALSTARTTIME_GMT"] = pd.to_datetime(
        data["INTERVALSTARTTIME_GMT"])
    data['hour'] = data["INTERVALSTARTTIME_GMT"].dt.hour
    hourly_lmp = data.groupby('hour')['LMP'].mean().reset_index()
    fig = px.line(hourly_lmp,
                  x='hour',
                  y='LMP',
                  title="Fairness Index (LMP Over Time)")
    fig.update_layout(
        xaxis_title="hour_of_day",
        yaxis_title="LMP",
        paper_bgcolor='transparent',
        plot_bgcolor='transparent',
        xaxis=dict(showgrid=True,
                   showline=True,
                   zeroline=True,
                   linecolor='black',
                   tickcolor='black',
                   ticks='outside',
                   ticklen=5,
                   title_standoff=10),
        yaxis=dict(showgrid=True,
                   showline=True,
                   zeroline=True,
                   linecolor='black',
                   tickcolor='black',
                   ticks='outside',
                   ticklen=5,
                   title_standoff=10),
    )
    return fig

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
            fig.add_trace(go.Scatter(x=multi_cluster_df[0], y=multi_cluster_df[1], mode='markers', marker=dict(color='black', size=5), name='multiple_cluster', showlegend=False))



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
        # height=800,
        template="plotly_white",
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showticklabels=False, showgrid=False)
    )
    return fig

def draw_clusters_scatterplot_json(clusters, points, selected_indices=None):
    fig = draw_clusters_scatterplot(clusters, points, selected_indices)
    return fig.to_json()  # Serialize the entire figure, including legend and layout

def generate_objective_graph(data):
    objective_col = list(objective_functions.keys())[0]
    if not data.empty:
        objective_mean = data[objective_col].mean()
        objective_std = data[objective_col].std()
    else:
        objective_mean = 0
        objective_std = 0
    # fig = go.Figure(go.Indicator(
    #     mode="number",
    #     value=objective_value,
    #     title={"text": f"Mean {objective_col.capitalize()}"},
    #     number={"font":{"size":50}},
    #     domain={"x":[0,1], "y":[0,1]}
    # ))
    
    # target_max = objective_value * 1.2 if objective_value > 0 else 100
    
    fig = go.Figure(go.Indicator(
        mode = "number",
        value=objective_mean,
        # delta={"reference": objective_std,"valueformat":".2f"},
        title={"text": f"Standard Deviation: {objective_std:.2f} & <br> Mean:",
               "font":{"size": 15}},
        number ={"font": {"size": 50}, "valueformat":".2f"},
        domain={"x":[0,1], "y":[0,1]}
        # gauge={
        #     "axis" : {"range": [0, target_max]},
        #     "bar":{"color": "#2874b4"},
        #     "steps":[
        #         {"range": [0, target_max * 0.5], "color":"lightgray"},
        #         {"range": [target_max * 0.5, target_max], "color":"#B8B8B8"}
        #     ]
        # }
    ))

    fig.update_layout(
        width=250,
        height=200,
        # showlegend = True,
        font=dict(color="black", size=10),
        font_family="Helvetica",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=40, t=30, b=10))
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
                        # selected=dict(marker=dict(color='#2874b4')),
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
        yaxis=dict(titlefont=dict(size=20)),
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
    return html.Div(dcc.Graph(figure = fig))
    
def assign_cluster_data(df, clusters, selected, dvars):
    y_name = clusters.columns[0]
    data = pd.concat([
        df.loc[clusters.index[clusters[c] == i], dvars]\
            .assign(**{y_name:i}, ovar=c)
        for c in clusters
        for i in clusters[c].unique()
        if i != -1
    ])

    return data

# Callbacks
def register_callbacks(app: Dash):

    @app.callback(Output("graph3", "figure"), [
        Input("tabs-example-graph", "value"),
        Input({
            "type": "hyperparameter-dropdown",
            "key": ALL
        }, "value"),
        Input("location-dropdown", "value")
    ])
    def update_objective_graph(selected_tab, hyperparam_values, sel_location):
        if selected_tab == "tab-3-example-graph" and sel_location is None:
            return blank_figure()
        if selected_tab == "tab-3-example-graph":
            if not hyperparam_values or all(value is None
                                          for value in hyperparam_values):
                return generate_objective_graph(csv_data)
                
            filtered_data = csv_data.copy() 
        if sel_location:
            filtered_data = filtered_data[filtered_data['location'].isin(sel_location)]
        
        hyper_keys = [key for key in hyperparameters.keys() if key != "other_cols"] 
        for i, key in enumerate(hyper_keys): 
            if i < len(hyperparam_values) and hyperparam_values[i]:
                filtered_data = filtered_data[filtered_data[key].isin(hyperparam_values[i])]
            
                return generate_objective_graph(filtered_data)
                
        return blank_figure()
        
    @app.callback(Output("sliders3", "children", allow_duplicate=True), [
        Input("tabs-example-graph", "value"),
        Input("location-dropdown","value"),
        Input({
            "type": "hyperparameter-dropdown",
            "key": ALL
        }, "value")
    ],
                  prevent_initial_call=True)
    def update_decision_space_sliders(selected_tab, sel_location,hyperparameter_values):
        if selected_tab == "tab-3-example-graph":
            filtered_data = csv_data.copy()
            if sel_location:
                if isinstance(sel_location,list):
                    filtered_data = filtered_data[filtered_data["location"].isin(sel_location)]
                else:
                    filtered_data=filtered_data[filtered_data["location"] == sel_location]
            
            if hyperparameter_values:
                for i, key in enumerate(hyperparameters.keys()):
                    if key == "other_cols":
                        continue
                    if len(hyperparameter_values) > i and hyperparameter_values[i]:
                        filtered_data = filtered_data[filtered_data[key].isin(hyperparameter_values[i])]
            return generate_decision_space_sliders(filtered_data)
        return []

    @app.callback(
        Output("hyperparameter-dropdowns", "children"),
        Input("tabs-example-graph", "value")
    )
    def display_hyperparameter(selected_tab):
        if selected_tab == "tab-3-example-graph":
            return get_hyperparameter_dropdown()
        return []

    @app.callback( Output('graph4', 'figure'), [Input('location-dropdown', 'value'), Input({"type":"hyperparameter-dropdown", "key":ALL},"value")],prevent_initial_call=False)
    def update_cluster_scatterplot(sel_location, hyperparam_values): 
        filtered_data = csv_data.copy() 
        if sel_location:
            filtered_data = filtered_data[filtered_data['location'].isin(sel_location)]
        
        hyper_keys = [key for key in hyperparameters.keys() if key != "other_cols"] 
        for i, key in enumerate(hyper_keys): 
            if i < len(hyperparam_values) and hyperparam_values[i]:
                filtered_data = filtered_data[filtered_data[key].isin(hyperparam_values[i])]
        
        updated_clusters = filtered_data[['location']] 
        # Also update the corresponding points (using the same indices as filtered_data). 
        updated_points = points.loc[filtered_data.index] # Draw and return an updated cluster scatterplot. 
        return draw_clusters_scatterplot(updated_clusters, updated_points)
    
    @app.callback(Output("time-series-graph", "figure"),
                  Input("location-dropdown", "value"))
    def update_time_series(location):
        if not location:
            return blank_figure()
        return generate_time_series(location)

    @app.callback(Output("fairness-index-graph", "figure"), [
        Input("time-series-graph", "selectedData"),
        Input("tabs-example-graph", "value")
    ])
    def update_fairness_index(selected_data, selected_tab):
        if selected_tab != "tab-3-example-graph":
            return blank_figure()

        if not os.path.exists(LMP_CSV_PATH):
            return blank_figure()

        data = pd.read_csv(LMP_CSV_PATH)
        if data.empty:
            return blank_figure()

        data["INTERVALSTARTTIME_GMT"] = pd.to_datetime(
            data["INTERVALSTARTTIME_GMT"])
        data['hour'] = data["INTERVALSTARTTIME_GMT"].dt.hour
        hourly_lmp = data.groupby('hour')['LMP'].mean().reset_index()

        filtered_lmp = hourly_lmp
        #Filter data based on selected range
        if selected_data and "range" in selected_data:
            range_start, range_end = selected_data["range"]["x"]
            filtered_lmp = hourly_lmp[(hourly_lmp['hour'] >= range_start)
                                      & (hourly_lmp['hour'] <= range_end)]
            
        fig = px.line(filtered_lmp, x='hour', y='LMP')
        fig.update_layout(paper_bgcolor='rgb(0,0,0,0)',
                          plot_bgcolor='rgb(0,0,0,0)',
                          xaxis=dict(showgrid=False,
                                     showline=True,
                                     zeroline=True,
                                     linecolor='black',
                                     tickcolor='black',
                                     ticks='outside',
                                     ticklen=5,
                                     title_standoff=10),
                          yaxis=dict(showgrid=False,
                                     showline=True,
                                     zeroline=True,
                                     linecolor='black',
                                     tickcolor='black',
                                     ticks='outside',
                                     ticklen=5,
                                     title_standoff=10))

        return fig