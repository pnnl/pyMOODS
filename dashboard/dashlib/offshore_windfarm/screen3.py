external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
import json, os
import pandas as pd
import plotly.express as px
import numpy as np
from dash import Dash, dcc, html, Input, Output
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

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

# location_options = mocodo_data["input_parameters"]["location"]["values"]
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


# print("Loading mocodo data: ")
# print(mocodo_data)
# print("Loading csv data...")
# print(csv_data.head())
def blank_figure():
    fig = go.Figure(go.Line(x=[], y=[]))
    fig.update_layout(template=None)
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False,title_standoff=5)
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False)

    return fig


# Generate Dropdown Options for Hyperparameters
def get_hyperparameter_dropdown():
    dropdowns = []
    for key, param in hyperparameters.items():
        if key != "other_cols":  # Skip 'other_cols'
            dropdown = dcc.Dropdown(
                id={
                    "type": "hyperparameter-dropdown",
                    "key": key
                },
                options=[{
                    'label': value,
                    'value': value
                } for value in param.get('values', [])],
                value=param.get('values', []),  # Default selected values
                multi=True,  # Multi-value selection
                placeholder=f'Select {param["name"]}...',
                style={
                    'width': '90%',
                    'height': '20%',
                    'maxHeight': '150px',
                    # 'overflowY': 'auto',
                    'margin': '5px 0',
                })
            dropdowns.append(
                html.Div(
                    [
                        html.Label(param["name"], style={'fontSize': '15px'}),
                        dropdown
                    ],
                    style={
                        #  'marginBottom': '20px',
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
        value="COTTONWOOD",
        placeholder='Select Location...',
        style={
            'width': '90%',
            'height': '20%',
            'maxHeight': '150px',
            # 'overflowY': 'auto',
            'margin': '5px 0'
        })


Data_folder = "/data"


def generate_time_series(location):
    if location not in LOCATIONS_FILES:
        return blank_figure()

    file_path = LOCATIONS_FILES[location]

    # try:
    data = pd.read_csv(file_path, header=1)
    # print(data.head())
    # fig = px.line(
    #     x = x_axis_label,
    #     y = y_axis_label,
    #     title = f"Wind Speed TimeSeries for {location}"
    # )
    hourly_windSpeed = data.groupby(
        'Hour')['wind speed at 100m (m/s)'].mean().reset_index()

    fig = px.line(hourly_windSpeed,
                  x="Hour",
                  y="wind speed at 100m (m/s)",
                  title=f"Wind Speed TimeSeries for {location}")

    fig.update_layout(
        xaxis_title="Hour",
        yaxis_title="Wind Speed (m/s)",
        dragmode='select',
        selectdirection='h',
        # template = "plotly white",
        paper_bgcolor='rgb(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template='simple_white',
        title={
            'x':0.5,
            'xanchor' : 'center',
            'y':0.9,
            'yanchor' : 'top',
            'font':{
                'size':14,
                'color':'black'
            }
        }
    )
    
    fig.update_xaxes(rangeslider_visible= True,rangeslider_thickness=0.2
                     )
    
    return fig
    # except Exception as e:
    #     return blank_figure()


def generate_fairness_index():
    if not os.path.exists(LMP_CSV_PATH):
        return blank_figure()
    data = pd.read_csv(LMP_CSV_PATH)
    if data.empty:
        return blank_figure()
    data["INTERVALSTARTTIME_GMT"] = pd.to_datetime(
        data["INTERVALSTARTTIME_GMT"])
    # data = data.rename(columns={"INTERVALSTARTTIME_GMT":"hour_of_day", "LMP": "lmp"})
    data['hour'] = data["INTERVALSTARTTIME_GMT"].dt.hour
    hourly_lmp = data.groupby('hour')['LMP'].mean().reset_index()
    # print("LMP data", data.head())
    fig = px.line(hourly_lmp,
                  x='hour',
                  y='LMP',
                  title="Fairness Index (LMP Over Time)")
    fig.update_layout(xaxis_title="hour_of_day",
                      yaxis_title="LMP",
                    #   template="simply_white",
                      paper_bgcolor='transparent',
                      plot_bgcolor='transparent',
                    #   margin="5px 0",
                      xaxis=dict(showgrid=True,showline= True, zeroline= True, linecolor='black', tickcolor='black', ticks='outside', ticklen=5, title_standoff=10),
                      yaxis=dict(showgrid=True,showline= True, zeroline= True, linecolor='black', tickcolor='black', ticks='outside', ticklen=5, title_standoff=10))
    return fig


# Generate Objective Space Graph
def generate_objective_graph(data):
    objective_col = list(objective_functions.keys())[0]
    # cost_col = "cost"
    num_points = len(data)  #Number of rows
    constant_y_val = 0
    y_val = [0] * num_points
    fig = px.scatter(data, x=objective_col, y=y_val)
    # fig = px.line(data, x=objective_col, y=data.index)
    # obj_val = list(objective_functions.values())[0]
    # fig= px.line(data, x="objective", y= obj_val)
    fig.update_layout(
        width=500,
        height=145,
        dragmode='select',
        # legend = dict(
        #                 font=dict( family="Courier", size=18, color="black"),
        #                 bgcolor = 'white', bordercolor="Black", borderwidth=1
        #             ),
        xaxis=dict(
            title="Total Cost",
            #    rangeslider_visible=True,
            showgrid=True,
            showline=True,
            zeroline=False,
            linewidth=2,
            linecolor='black',
            title_font=dict(size=18),
            title_standoff=5,
            automargin=True),
        yaxis=dict(
            title=None,
            showgrid=False,
            zeroline=True,
            showticklabels=False,
            title_standoff=5,
            automargin=False,
            #    range = [0.9,0.9]
        ),
        font=dict(color="black", size=18),
        clickmode='event+select',
        font_family="Helvetica",
        # margin=dict(l=20, r=20, t=0, b=20),
        paper_bgcolor='rgb(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=50, r=50, t=50, b=50))
    # fig.show()
    fig.update_traces(marker=dict(size=20))
    return fig


# Generate Decision Space Sliders
def generate_decision_space_sliders(data):
    updated_sliders_offshore = []
    for var, details in decision_variables.items():
        min_val = data[var].min()
        max_val = data[var].max()
        default_value = min_val
        updated_sliders_offshore.append(
            html.Div(
                [
                    html.Label(f'{details["name"]} ({var})',
                               className="slider-label"),
                    dcc.Slider(
                        id={
                            'type': 'ds-sliders',
                            'index': f'slider-{var}'
                        },
                        min=min_val,
                        max=max_val,
                        step=0.01,
                        value=default_value,
                        marks={
                            i: f'{i: .2f}'
                            for i in np.arange(min_val, max_val + 0.1, 0.25)
                        },
                        tooltip={
                            "placement": "bottom",
                            "always_visible": True,
                        },
                        className="slider-2",
                        # pushable=1,
                    ),
                ],
                style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'width': '100%',
                },
            ))
    return updated_sliders_offshore


def apply_filter_to_data(data, dropdown_values):
    for param, values in dropdown_values.items():
        if values:
            data = data[data[param].isin(values)]
    return data


# Callbacks
def register_callbacks(app: Dash):
    # @app.callback(
    #     Output("cluster-dropdown", "options"),
    #     Input("tabs-example-graph", "value"),
    # )
    # def update_hyperparameter_dropdown(selected_tab):
    #     if selected_tab == "tab-3-example-graph":
    #         return get_hyperparameter_dropdown()
    #     return []

    @app.callback(Output("graph3", "figure"), [
        Input("tabs-example-graph", "value"),
        Input({
            "type": "hyperparameter-dropdown",
            "key": ALL
        }, "value")
    ])
    def update_objective_graph(selected_tab, dropdown_values):
        # print(
        #     f"update_obj_graoh triggered with tab:{selected_tab}, dropdown values:{dropdown_values}"
        # )
        # print(f"Type of dropdown: {type(dropdown_values)}")
        if selected_tab == "tab-3-example-graph":
            if not dropdown_values or all(value is None
                                          for value in dropdown_values):
                return generate_objective_graph(csv_data)
            filtered_data = csv_data.copy()
            if dropdown_values:
                for i, values in enumerate(dropdown_values):
                    param_key = list(hyperparameters.keys())[i]
                    if values:
                        filtered_data = filtered_data[
                            filtered_data[param_key].isin(values)]
                return generate_objective_graph(filtered_data)
        return blank_figure()

    @app.callback(Output("sliders3", "children", allow_duplicate=True), [
        Input("tabs-example-graph", "value"),
        Input({
            "type": "hyperparameter-dropdown",
            "index": ALL
        }, "value")
    ],
                  prevent_initial_call=True)
    def update_decision_space_sliders(selected_tab, hyperparameter_values):
        # print(f" sliders:{selected_tab}")
        if selected_tab == "tab-3-example-graph":
            filtered_data = csv_data.copy()
            for param_key, param_values in zip(hyperparameters.keys(),
                                               hyperparameter_values):
                if param_key != "other_cols" and param_values:
                    filtered_data = filtered_data[
                        filtered_data[param_key].isin(param_values)]
            return generate_decision_space_sliders(filtered_data)
        return []

    @app.callback(
        Output("hyperparameter-dropdowns", "children"),
        # Output("inputparameter-dropdowns", "children"),
        Input("tabs-example-graph", "value"),
    )
    def display_hyperparameter(selected_tab):
        # print(f" Tab:{selected_tab}")
        if selected_tab == "tab-3-example-graph":
            return get_hyperparameter_dropdown()
        return []

    @app.callback(Output("sliders3", "children"),
                  Input("graph3", "selectedData"),
                  State("sliders3", "children"))
    def update_sliders_on_click(selected_data, current_sliders):
        if selected_data is None:
            print("No point selected on graph")
            return current_sliders

        selected_points = selected_data.get("points", [])
        if not selected_points:
            return current_sliders

        selected_idx = selected_points[0]["pointIndex"]
        selected_row = csv_data.iloc[selected_idx]
        print(f"Selected data: {selected_row}")

        updated_sliders_offshore = []
        for var, details in decision_variables.items():
            min_val = csv_data[var].min()
            max_val = csv_data[var].max()
            selected_value = selected_row[var]
            updated_sliders_offshore.append(
                html.Div(
                    [
                        html.Label(f'{details["name"]} ({var})',
                                   className="slider-label"),
                        dcc.Slider(
                            id={
                                'type': 'ds-sliders',
                                'index': f'slider-{var}'
                            },
                            min=min_val,
                            max=max_val,
                            step=0.01,
                            value=selected_value,
                            marks={
                                i: f'{i: .2f}'
                                for i in np.arange(min_val, max_val +
                                                   0.1, 0.25)
                            },
                            tooltip={
                                "placement": "bottom",
                                "always_visible": True,
                            },
                            className="slider-2",
                            # pushable=1,
                        ),
                    ],
                    style={
                        'display': 'flex',
                        'alignItems': 'center',
                        'width': '100%',
                    },
                ))
        return updated_sliders_offshore

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
            filtered_lmp = hourly_lmp[(hourly_lmp['hour'] >= range_start) & (hourly_lmp['hour'] <= range_end)]
            print(f"Selected Range:{range_start} to {range_end}")
            
        # elif selected_data and "points" in selected_data:
        #     selected_hours = [point["x"] for point in selected_data["points"]]
        #     hourly_lmp = hourly_lmp[hourly_lmp['hour'].isin(selected_hours)]

        print("Filtered LMP Data:\n", filtered_lmp)
        fig = px.line(filtered_lmp, x='hour', y='LMP')
        fig.update_layout(
                      paper_bgcolor='rgb(0,0,0,0)',
                      plot_bgcolor='rgb(0,0,0,0)',
                      xaxis=dict(showgrid=False,showline= True, zeroline= True, linecolor='black', tickcolor='black', ticks='outside', ticklen=5, title_standoff=10),
                      yaxis=dict(showgrid=False,showline= True, zeroline= True, linecolor='black', tickcolor='black', ticks='outside', ticklen=5, title_standoff=10))
    
        return fig

   
