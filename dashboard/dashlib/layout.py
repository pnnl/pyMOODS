import base64
import json
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from .components import blank_figure

interface_layout = dbc.Container(
    [
        dbc.Row([
            dbc.Col(html.Div(
                html.Img(className='image',
                         src="assets/PNNL-logo-16-9.png",
                         style={
                             'width': '170px',
                             'height': '120px'
                         })),
                    width=2),
            dbc.Col(html.H1(
                children=
                "pyMOODS: Multi-Objective Optimization Decision Support System",
                style={
                    "fontWeight": "400",
                    "textAlign": "center",
                    "marginTop": "1rem"
                }),
                    width=8),
            dbc.Col(html.Div(html.Img(src="assets/E-COMP_logo (3).png")),
                    width=2),
        ],
                className="header-row"),
        dcc.Store(id="stored-df"),
        dcc.Store(id="data-generated"),
        dbc.Row(
            [
                dbc.Col(html.Div([
                    html.H3("Data Input"),
                    html.Hr(),
                    dbc.Label("Test:", style={'fontSize': '20px'}),
                    dcc.Dropdown(id='test-dropdown',
                                 options=[
                                     {
                                         'label': 'DTLZ4',
                                         'value': 'DTLZ4'
                                     },
                                     {
                                         'label': 'DTLZ3',
                                         'value': 'DTLZ3'
                                     },
                                 ],
                                 value='DTLZ4'),
                    dbc.Label('#Decision variables:',
                              style={
                                  'marginTop': '1rem',
                                  'fontSize': '20px'
                              }),
                    dbc.Input(
                        id="num-decision-vars",
                        placeholder="Enter the number of Decision variables",
                        type="number", 
                        min=2, max=20
                        ),
                    dbc.Label('#Objective variables:',
                              style={
                                  'marginTop': '1rem',
                                  'fontSize': '20px'
                              }),
                    dbc.Input(
                        id="num-objective-vars",
                        placeholder="Enter the number of Objective variables",
                        type="number", 
                        min=2,max=20
                        ),
                    dbc.Button('Generate Data', 
                                       color="dark",
                                       size="lg",
                                id='generated-dtlz4-button',
                                n_clicks=0,style={
                                  'marginTop': '2rem',
                                #   'fontSize': '20px'
                              } ),
                    dcc.Upload(
                        id="upload-data",
                        children=html.Div([
                            # html.Div(html.H3("DATA UPLOAD")),
                            html.Hr(),
                            html.Div(html.H4("OR")),
                            dbc.Button('Upload Pareto Front',
                                    #    outline=True,
                                       color="dark",
                                       size="lg"),
                            html.Div(id='summary-table'),
                        ]),
                        multiple=True,
                    ),
                ],
                                 className='upload-section'),
                        width={'size': 3},
                        className='h-75 d-inline-block',
                        style={
                            'height': 'calc(100vh-150px)',
                            'overflow': 'hidden'
                        }),
                dbc.Col(
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
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        html.H4(
                                                            "Objective Space",
                                                            style={
                                                                "fontWeight":
                                                                "600",
                                                                "fontFamily":
                                                                "Helvetica",
                                                                "margin":
                                                                "40px",
                                                                "textAlign":
                                                                "center"
                                                                # "marginLeft":"15rem"
                                                            }),
                                                        width=6),
                                                    dbc.Col(
                                                        html.H4(
                                                            "Decision Space",
                                                            style={
                                                                "fontWeight":
                                                                "600",
                                                                "fontFamily":
                                                                "Helvetica",
                                                                "textAlign":
                                                                "center",
                                                                "margin":
                                                                "40px"
                                                                # "margin":"50px", "marginLeft":"15rem"
                                                            }),
                                                        width=6)
                                                ],
                                                className=
                                                "my-custom-container-style",
                                                # id="container-row"
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        children=[
                                                            dcc.Graph(
                                                                figure=
                                                                blank_figure(),
                                                                id='graph1')
                                                        ],
                                                        width=6),
                                                    dbc.Col(
                                                        html.Div(id="sliders"),
                                                        # className="sliders-container"
                                                        width=6),
                                                ],
                                                className=
                                                "my-custom-container-style"),
                                            # ]),
                                            dbc.Row(
                                                [
                                                    dbc.Col([
                                                        dbc.Card(
                                                            dbc.CardBody([
                                                                html.
                                                                H4("Plot Description",
                                                                   className=
                                                                   "card-title"
                                                                   )
                                                            ]))
                                                    ],
                                                            className=
                                                            "card-container"
                                                            # width=6
                                                            ),
                                                    dbc.Col([
                                                        dbc.Card(
                                                            dbc.CardBody([
                                                                html.
                                                                H4("Fairness Index (Future Capability)",
                                                                   className=
                                                                   "card-title2"
                                                                   )
                                                            ]))
                                                    ],
                                                            # width=6
                                                            ),
                                                ],
                                                className="align-cards",
                                                # style={"height":"calc(100vh - 150px)","overflow":"hidden"}
                                            )
                                        ],
                                        fluid=True,
                                        #   style={"height":"calc(100vh - 50px)","overflow":"hidden"}
                                    )
                                ]),
                            dcc.Tab(
                                label='MOP Structure',
                                value='tab-2-example-graph',
                                className='custom-tab',
                                selected_className='custom-tab--selected',
                                children=[
                                    dbc.Container(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        html.H4(
                                                            "Objective Space",
                                                            style={
                                                                "fontWeight":"600",
                                                                "fontFamily":"Helvetica",
                                                                "margin": "40px",
                                                                "textAlign":"center"
                                                                # "marginLeft":"15rem"
                                                            }),
                                                        width=6),
                                                    dbc.Col(
                                                        html.H4(
                                                            "Decision Space",
                                                            style={
                                                                "fontWeight":"600",
                                                                "fontFamily":"Helvetica",
                                                                "textAlign": "center",
                                                                "margin":"40px"
                                                                # "margin":"50px", "marginLeft":"15rem"
                                                            }),
                                                        width=6)
                                                ],
                                                className=
                                                "my-custom-container-style",
                                                # id="container-row"
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        dcc.Graph(
                                                            id=
                                                            "mop-objective-graph",
                                                            figure=blank_figure(
                                                            )),
                                                        width=6),
                                                    dbc.Col(
                                                        dcc.Graph(
                                                            id=
                                                            "mop-decision-graph",
                                                            figure=blank_figure(
                                                            )),
                                                        width=6),
                                                ],
                                                className=
                                                "my-custom-container-style"),
                                            # ]),
                                            dbc.Row(
                                                [
                                                    dbc.Col([
                                                        dbc.Card(
                                                            dbc.CardBody([
                                                                html.
                                                                H4("Plot Description",
                                                                   className=
                                                                   "card-title"
                                                                   )
                                                            ]))
                                                    ],
                                                            className=
                                                            "card-container"
                                                            # width=6
                                                            ),
                                                    dbc.Col([
                                                        dbc.Card(
                                                            dbc.CardBody([
                                                                html.
                                                                H4("Fairness Index (Future Capability)",
                                                                   className=
                                                                   "card-title2"
                                                                   )
                                                            ]))
                                                    ],
                                                            # width=6
                                                            ),
                                                ],
                                                className="align-cards",
                                                # style={"height":"calc(100vh - 150px)","overflow":"hidden"}
                                            )
                                        ],
                                        fluid=True,
                                        #   style={"height":"calc(100vh - 50px)","overflow":"hidden"}
                                    )
                                ]),
                            dcc.Tab(
                                label='Model Reasoning',
                                value='tab-3-example-graph',
                                className='custom-tab',
                                selected_className='custom-tab--selected',
                                children=[
                                    dbc.Container(
                                        [
                                            # dbc.Container([
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        html.H4(
                                                            "Objective Space",
                                                            style={
                                                                "fontWeight":
                                                                "600",
                                                                "fontFamily":
                                                                "Helvetica",
                                                                "margin":
                                                                "40px",
                                                                "textAlign":
                                                                "center"
                                                                # "marginLeft":"15rem"
                                                            }),
                                                        width=6),
                                                    dbc.Col(
                                                        html.H4(
                                                            "Decision Space",
                                                            style={
                                                                "fontWeight":
                                                                "600",
                                                                "fontFamily":
                                                                "Helvetica",
                                                                "textAlign":
                                                                "center",
                                                                "margin":
                                                                "40px"
                                                                # "margin":"50px", "marginLeft":"15rem"
                                                            }),
                                                        width=6)
                                                ],
                                                className=
                                                "my-custom-container-style",
                                                # id="container-row"
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        children=[
                                                            dcc.Graph(
                                                                figure=
                                                                blank_figure(),
                                                                id='graph3')
                                                        ],
                                                        width=6),
                                                    dbc.Col(
                                                        html.Div(
                                                            id="sliders3"),
                                                        # className="sliders-container"
                                                        width=6),
                                                ],
                                                className=
                                                "my-custom-container-style"),
                                            # ]),
                                            dbc.Row(
                                                [
                                                    dbc.Col([
                                                        dbc.Card(
                                                            dbc.CardBody([
                                                                html.
                                                                H4("Plot Description",
                                                                   className=
                                                                   "card-title"
                                                                   )
                                                            ]))
                                                    ],
                                                            className=
                                                            "card-container"
                                                            # width=6
                                                            ),
                                                    dbc.Col([
                                                        dbc.Card(
                                                            dbc.CardBody([
                                                                html.
                                                                H4("Fairness Index (Future Capability)",
                                                                   className=
                                                                   "card-title2"
                                                                   )
                                                            ]))
                                                    ],
                                                            # width=6
                                                            ),
                                                ],
                                                className="align-cards",
                                                # style={"height":"calc(100vh - 150px)","overflow":"hidden"}
                                            )
                                        ],
                                        fluid=True,
                                        #   style={"height":"calc(100vh - 50px)","overflow":"hidden"}
                                    )
                                ]),
                        ],
                        colors={
                            "border": "white",
                            "primary": "red",
                            "background": "#98A5C0"
                        },
                    ),
                    width={'size': 9
                           # 'offset': 0
                           },
                ),
            ],
            # className="content-row"
        ),
    ],
    className="main-container",
    fluid=True)
