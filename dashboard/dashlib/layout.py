import base64
import json
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from .components import blank_figure

interface_layout = html.Div([
    dbc.Row([
        dbc.Col(
            html.Div(
                html.Img(
                    className='image',
                    src="assets/PNNL-logo-16-9.png",
                    style={
                        'position': 'absolute',
                        'top': '5px',
                        'left': '40px',
                        'width': '115px',
                        'height': '100px',
                        #  'border':'20px none white',
                        #  'padding':'4px',
                        'margin-left': '1px',
                        'margin-right': '1px',
                    }),
                className='box'),
            width=2),
        dbc.Col(html.H1(
            children=
            "pyMOODS: Multi-Objective Optimization Decision Support System",
            style={
                "fontWeight": "400",
                "textAlign": "center",
                "marginTop": "1rem",
            },
        ),
                width=8),
        dbc.Col(
            html.Img(src="assets/E-COMP_logo (3).png",
                     style={
                         'position': 'absolute',
                         'top': '5px',
                         'right': '40px',
                         'width': '300px',
                         'height': '110px'
                     }))
    ]),
    dcc.Store(id="stored-df"),
    html.Div([
        dcc.Upload(
            id="upload-data",
            children=html.Div([
                html.Div(html.H3("DATA UPLOAD")),
                html.Hr(),
                dbc.Button('Upload Pareto Front',
                           outline=True,
                           color="dark",
                           size="lg"),
                html.Div(id='summary-table'),
            ]),
            style={
                'borderTop': '200px',
                "position": "fixed",
                'borderRadius': '5px',
                "top": '7.4rem',
                "left": "1rem",
                "bottom": '2px',
                "textAlign": "center",
                "width": "30rem",
                "padding": "8rem 1.5rem 50rem 1rem",
                "color": "black",
                "fontWeight": "bolder",
                "backgroundColor": "#fcba03",
                "fontFamily": "Helvetica",
            },
            multiple=True,
        ),
        # html.Div(id='summary-table'),
    ]),
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
                            dbc.Row([
                                dbc.Col(),
                                dbc.Col(html.H4("Objective Space",
                                                style={
                                                    "fontWeight": "600",
                                                    "borderTop": "120px",
                                                    "paddingTop": "40px",
                                                    'fontFamily': "Helvetica"
                                                }),
                                        width=5),
                                dbc.Col(html.H4("Decision Space",
                                                style={
                                                    "fontWeight": "600",
                                                    "borderTop": "120px",
                                                    "paddingTop": "40px",
                                                    'fontFamily': "Helvetica",
                                                    'marginLeft': '100px'
                                                }),
                                        width=5)
                            ],
                                    className="my-custom-container-style"),
                            dbc.Row(
                                [
                                    # dbc.Col(width=2),
                                    dbc.Col(
                                        id="graph-container",
                                        children=[
                                            dcc.Graph(
                                                figure=blank_figure(),
                                                # style={
                                                #     "backgroundColor":
                                                #     "transparent"
                                                # },
                                                id='graph1')
                                        ]),
                                    dbc.Col(html.Div(id="sliders")),
                                ],
                                className="my-custom-container-style"),
                            dbc.Row(
                                [
                                    dbc.Col([
                                        dbc.Card(
                                            dbc.CardBody([
                                                html.H4(
                                                    "Plot Description",
                                                    className="card-title"),
                                                # Add interpretation content here
                                            ]))
                                    ]),
                                    dbc.Col([
                                        dbc.Card(
                                            dbc.CardBody([
                                                html.
                                                H4("Fairness Index (Future Capability)",
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
