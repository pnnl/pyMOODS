from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

from .components import blank_figure

interface_layout = html.Div([
    dcc.Store(id="stored-df"),
    html.Div(id='placeholder'),
    html.H1(
        children="pyMOODS: Multi-Objective Optimization Decision Support System",
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
                                html.Div(
                                    id="graph-container",
                                    children=[dcc.Graph(figure=blank_figure(), id='graph1')]
                                ),
                                html.Div(id="sliders"),
                                html.Button("Objective Space"),
                                html.Button("Decision Space",
                                            style={"marginLeft": "600px", "marginBottom": "1px"}),
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