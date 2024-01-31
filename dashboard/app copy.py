import base64
import json
import pandas as pd
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from pymoo.problems import get_problem

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
)

app.layout = html.Div([
    dcc.Store(id="stored-df"),
    html.H1(
        children="PYMOODS: Multi-Objective Optimization Decision Support System",
        style={
            "fontWeight": "400",
            "textAlign": "center",
            "marginTop": "1rem",
        },
    ),
    dcc.Upload(
        id="upload-data",
        children=html.Div([
            html.Div(html.H3("Data Upload"), style={"left": "1rem"}),
            html.Hr(),
            dbc.Button('Upload File', outline=True, color="dark", size="lg")
        ]),
        style={
            'borderTop': '200px',
            "position": "fixed",
            'borderRadius': '10px',
            "top": '7.4rem',
            "bottom": '1px',
            "left": "0.8rem",
            "width": "23rem",
            "padding": "8rem 1.5rem 50rem 2.5rem",
            "color": "black",
            "fontWeight": "bolder",
            "backgroundColor": "#fcba03",  # Change background color
        },
        multiple=True,
    ),
    dcc.Tabs(
        id="tabs-example-graph",
        value='tab-1-example-graph',
        children=[
            dcc.Tab(
                label='Global Dominance',
                value='tab-1-example-graph',
                className='custom-tab',
                selected_className='custom-tab--selected',
                children=[
                    dbc.Container(
                        [
                            html.Div([
                                html.Div(id="graph-container"),
                                html.Div(id="sliders"),
                                html.Button("Objective Space"),
                                html.Button("Decision Space",
                                            style={"margin-left": "600px", "margin-bottom": "1px"}),
                            ],
                                className="my-custom-container-style"),
                            dbc.Row(
                                [
                                    dbc.Col([
                                        dbc.Card(
                                            dbc.CardBody([
                                                html.H4(
                                                    "AI-Interpretation",
                                                    className="card-title"),
                                                # Add interpretation content here
                                            ]))
                                    ]),
                                    dbc.Col([
                                        dbc.Card(
                                            dbc.CardBody([
                                                html.H4(
                                                    "Fairness Index",
                                                    className="card-title2"),
                                                # Add Fairness Index content here
                                            ]))
                                    ]),
                                ],
                                className="align-cards"),
                        ], ),
                ]),
            dcc.Tab(label='MOP Structure',
                    value='tab-2-example-graph',
                    className='custom-tab',
                    selected_className='custom-tab--selected'),
            dcc.Tab(label='Model Reasoning',
                    value='tab-3-example-graph',
                    className='custom-tab',
                    selected_className='custom-tab--selected'),
        ],
        colors={
            "border": "white",
            "primary": "red",
            "background": "#98A5C0"
        },
    ),
])


def parse_data(contents, filename):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    try:
        json_data = json.loads(decoded)
        if isinstance(json_data, list):
            df = pd.DataFrame(json_data)

            # Categorize variables into 'Decision Variables' and 'Objective Functions'
            decision_variables = {key: df[key].tolist() for key in df.columns if key.startswith('x')}
            objective_functions = {key: df[key].tolist() for key in df.columns if key.startswith('f')}

            return df, decision_variables, objective_functions

    except Exception as e:
        print(e)
        return None, None, None


def generate_slider_callback(col, min_val, max_val):
    @app.callback(Output(f'slider-{col}', 'value'),
                  Input('graph1', 'clickData'),
                  State('stored-df', 'data'),
                  prevent_initial_call=True)
    def slider_output(click_data, my_data):
        if click_data and my_data:
            df = pd.DataFrame(my_data)
            f1_point = click_data['points'][0]['x']
            f2_point = click_data['points'][0]['y']
            dff = df[(df.f1 == f1_point) & (df.f2 == f2_point)]
            if not dff.empty and col in dff.columns:
                return dff[col].values[0]
        return 0


@app.callback(Output("graph-container", "children"),
              Output("stored-df", "data"),
              Output("sliders", "children"), [
                  Input("upload-data", "contents"),
                  Input("upload-data", "filename"),
                  Input('tabs-example-graph', 'value')
              ],
              prevent_initial_call=True)
def update_output(contents, filename, tab):
    if contents is not None:
        contents = contents[0]
        filename = filename[0]
        df, decision_variables, objective_functions = parse_data(contents, filename)

        if df is not None:
            # Save categorized data to "categorized_data.json"
            categorized_data = {
                "Decision Variables": {key: {"values": value, "min": 0, "max": 1} for key, value in decision_variables.items()},
                "Objective Functions": {key: value for key, value in objective_functions.items()},
            }
            with open("categorized_data.json", "w") as outfile:
                json.dump(categorized_data, outfile, cls=NumpyEncoder, indent=4)

            fig = gen_graph(df, tab)
            graph = dcc.Graph(figure=fig, id='graph1')
            sliders = [
                html.Div([
                    html.Label(col,
                               style={
                                   "font-size": "27px",
                                   "font-weight": "bold"
                               }),
                    dcc.Slider(
                        id=f'slider-{col}',
                        min=min_val,
                        max=max_val,
                        step=0.1,
                        marks={
                            i: f'{i: .2f}' for i in np.arange(min_val, max_val + 0.1, 0.1)
                        },
                        tooltip={
                            "placement": "bottom",
                            "always_visible": True
                        }),
                ]) for col, (min_val, max_val) in zip(decision_variables.keys(), [(0, 1)] * len(decision_variables))
            ]

            # Dynamically generate callback for each slider
            for col, (min_val, max_val) in zip(decision_variables.keys(), [(0, 1)] * len(decision_variables)):
                generate_slider_callback(col, min_val, max_val)

            return graph, df.to_dict('records'), sliders

    return dash.no_update, [], []


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def gen_graph(df, tab):
    fig = go.Figure()
    if (tab == 'tab-1-example-graph') and df is not None:
        if isinstance(df, pd.DataFrame):
            f_cols = [col for col in df.columns if col.startswith('f')]
            if len(f_cols) >= 2:
                x_column, y_column = f_cols[:2]
            else:
                print("Error: Insufficient columns starting with 'f'")
                return fig
            fig.add_trace(
                go.Scatter(
                    x=df[x_column],
                    y=df[y_column],
                    mode="markers",
                    marker={
                        'size': 10,
                        "color": "blue"
                    },
                    selected=go.scatter.Selected(marker={
                        'size': 25,
                        "color": "LightSeaGreen"
                    })))
        else:
            print("Invalid data format")
            return fig

        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        fig.update_layout(
            font=dict(color="black", size=22, family="Courier New"),
            clickmode='event+select',
            mapbox={
                'style': "stamen-terrain",
                'zoom': 6
            },
            hovermode='closest',
            xaxis_title='f1',
            yaxis_title='f2',
            font_color='black',
            font_family="Courier New",
            margin=dict(l=10, r=20, t=20, b=0),
            # title="Objective Space",
            paper_bgcolor='rgb(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)