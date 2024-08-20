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
                             'width': '172px',
                             'height': '120px'
                         })),
                    width=2),
            dbc.Col(html.H1(
                children=
                "pyMOODS: Multi-Objective Optimization Decision Support System",
                style={
                    "textAlign": "center",
                    "marginTop": "1rem"
                }),
                    width=8),
            dbc.Col(html.Div(
                html.Img(src="assets/E-COMP_logo (3).png",
                         style={
                             'width': '272px',
                             'height': '115px'
                         })),
                    width=2),
        ],
                className="header-row"),
        dcc.Store(id="stored-df"),
        dcc.Store(id="data-generated"),
        # html.Div(id="update-message", style={'color':'red', 'fontSize':'16px','marginTop':'3rem'}),
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.H5("Data Input"),
                            html.Hr(),
                            dbc.Label("Problem Statement:",
                                      style={'fontSize': '15px'}),
                            dcc.Dropdown(
                                id='test-dropdown',
                                options=[
                                    {
                                        'label':
                                        'DTLZ1',
                                        'value':
                                        'DTLZ1'
                                    },
                                    {
                                        'label':
                                        'DTLZ3',
                                        'value':
                                        'DTLZ3'
                                    },
                                    {
                                        'label':
                                        'Optimal Battery Size (Offshore Wind)',
                                        'value': 'RealTimeData'
                                    },
                                    {
                                        'label':
                                        'Optimal Battery Size (Offshore Wind) - 2',
                                        'value': 'RealTimeData2'
                                    },
                                ],
                                value='DTLZ1'),
                            dbc.Label('#Decision variables:',
                                      style={
                                          'marginTop': '1rem',
                                          'fontSize': '15px'
                                      }),
                            dbc.Input(id="num-decision-vars",
                                      placeholder=
                                      "Enter the number of Decision variables",
                                      type="number",
                                      size="sm",
                                      min=2,
                                      max=20),
                            dbc.Label('#Objective variables:',
                                      style={
                                          'marginTop': '1rem',
                                          'fontSize': '15px'
                                      }),
                            dbc.Input(
                                id="num-objective-vars",
                                placeholder=
                                "Enter the number of Objective variables",
                                type="number",
                                size="sm",
                                min=2,
                                max=20),
                            dbc.Row([
                                dbc.Col(dbc.Button('Generate Data',
                                                   color="dark",
                                                   size="xs",
                                                   id='generated-dtlz-button',
                                                   n_clicks=0,
                                                   style={'padding': '0.2rem'
                                                          }),
                                        width=5),
                                # dbc.Col(html.H6("OR"),
                                #         width=1,
                                #         style={
                                #             'marginTop': '2.1rem','paddingLeft':'0.1rem'
                                #         }),
                                dbc.Col(
                                    dcc.Upload(
                                        id="upload-data",
                                        children=html.Div([
                                            # html.Div(html.H3("DATA UPLOAD")),
                                            # html.Hr(),
                                            # html.Div(html.H4("OR")),
                                            dbc.Button(
                                                'Upload Pareto Front',
                                                #    outline=True,
                                                color="dark",
                                                size="xs",
                                                style={
                                                    'backgroundColor':
                                                    'lightSteelBlue',
                                                    'color': 'black',
                                                    'padding': '0.2rem'
                                                }),
                                            # html.Div(id='summary-table'),
                                        ]),
                                        multiple=True,
                                    ), )
                            ]),
                            # dbc.Button(
                            #     'Generate Data',
                            #     color="dark",
                            #     size="lg",
                            #     id='generated-dtlz-button',
                            #     n_clicks=0,
                            #     style={
                            #         'marginTop': '2rem',
                            #         #   'fontSize': '20px'
                            #     }),
                            #    dcc.Upload(
                            #     id="upload-data",
                            #     children=html.Div([
                            #         # html.Div(html.H3("DATA UPLOAD")),
                            #         html.Hr(),
                            #         html.Div(html.H4("OR")),
                            #         dbc.Button(
                            #             'Upload Pareto Front',
                            #             #    outline=True,
                            #             color="dark",
                            #             size="lg"),
                            #         html.Div(id='summary-table'),
                            #     ]),
                            #     multiple=True,
                            # ),
                            html.Hr(),
                            dbc.Label("Objective Weights:",
                                      style={'fontSize': '15px'}),
                            dbc.Input(
                                id="obj-weights-input",
                                placeholder=
                                "Enter the weight for Objective variables",
                                type="text",
                                size="sm"),
                            html.Div(id='summary-table'),
                            # dcc.Upload(
                            #     id="upload-data",
                            #     children=html.Div([
                            #         # html.Div(html.H3("DATA UPLOAD")),
                            #         html.Hr(),
                            #         html.Div(html.H4("OR")),
                            #         dbc.Button(
                            #             'Upload Pareto Front',
                            #             #    outline=True,
                            #             color="dark",
                            #             size="lg"),
                            #         html.Div(id='summary-table'),
                            #     ]),
                            #     multiple=True,
                            # ),
                        ],
                        className='upload-section'),
                    width={'size': 2},
                    className='h-75 d-inline-block',
                    style={
                        'height': 'calc(100vh-170px)',
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
                                                        [
                                                            html.
                                                            H4("Objective Space",
                                                               style={
                                                                   "fontWeight":
                                                                   "600",
                                                                   "fontFamily":
                                                                   "Helvetica",
                                                                   "margin":
                                                                   "20px 0 0 0",
                                                                   "textAlign":
                                                                   "center"
                                                               }),
                                                            html.
                                                            H6(id='obj-help',
                                                               style={
                                                                   'textAlign':
                                                                   'center'
                                                               }),
                                                            # html.Div([
                                                            #     dbc.Checklist(
                                                            #         id="use-cluster-toggle",
                                                            #         options=[{"label": "Color by cluster", "value":'cluster'}],
                                                            #         value=[],
                                                            #         inline=True,
                                                            #         switch=True,
                                                            #         style={'display':'none'}
                                                            #     ),
                                                            #     dcc.Dropdown(
                                                            #         id='cluster-dropdown',
                                                            #         options=[],
                                                            #         value=[],
                                                            #         multi=True,
                                                            #         placeholder='Select a cluster',
                                                            #         style={'display':'none'}
                                                            #     )
                                                            # ], style={'display':'flex', 'alignItems':'center'}),
                                                            dcc.Loading(
                                                                id=
                                                                'loading-graph',
                                                                children=[
                                                                    dcc.Graph(
                                                                        figure=
                                                                        blank_figure(
                                                                        ),
                                                                        id=
                                                                        'graph1',
                                                                        style={
                                                                            'height':
                                                                            '35vh'
                                                                        })
                                                                ],
                                                                target_components
                                                                ={
                                                                    'graph1':
                                                                    ['figure']
                                                                })
                                                        ],
                                                        width=6, 
                                                        id='graph-col'
                                                        ),
                                                    dbc.Col([
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
                                                                "20px 0 0 0"
                                                            }),
                                                        html.H6(
                                                            id='dec-help',
                                                            style={
                                                                'textAlign':
                                                                'center'
                                                            }),
                                                        html.Div(id="sliders"),
                                                    ],
                                                            width=6, 
                                                            id="radar-col"
                                                            ),
                                                    dbc.Alert(
                                                        'No data exists reflecting that change',
                                                        id='no-data-alert',
                                                        color='danger',
                                                        is_open=False,
                                                        dismissable=True,
                                                        duration=5000,
                                                        style={
                                                            'position':
                                                            'absolute',
                                                            'top': '15%',
                                                            'left': '50%',
                                                            'zIndex': 999
                                                        })
                                                ],
                                                className=
                                                "my-custom-container-style"),
                                            # id="container-row"
                                            dbc.Row([
                                                dbc.Col([
                                                    dbc.Card(
                                                        dbc.CardBody([
                                                            html.
                                                            H4("Plot Description",
                                                               className=
                                                               "card-title")
                                                        ]))
                                                ],
                                                        className=
                                                        "card-container"),
                                                dbc.Col([
                                                    dbc.Card(
                                                        dbc.CardBody([
                                                            html.
                                                            H4("Fairness Index (Future Capability)",
                                                               className=
                                                               "card-title2")
                                                        ]))
                                                ],
                                                        className=
                                                        "card2-container"),
                                            ],
                                                    className="align-cards")
                                            # style={"height":"calc(100vh - 150px)","overflow":"hidden"}
                                        ],
                                        fluid=True,
                                        className='dbc-container-style')
                                    #   style={"height":"calc(100vh - 50px)","overflow":"hidden"}
                                ]),
                            dcc.Tab(
                                label='MOP Structure',
                                value='tab-2-example-graph',
                                className='custom-tab',
                                selected_className='custom-tab--selected',
                                children=[
                                    dbc.Container(
                                        [
                                            dbc.Row([
                                                dbc.Col(html.H4(
                                                    "Objective Space",
                                                    style={
                                                        "fontWeight": "600",
                                                        "fontFamily":
                                                        "Helvetica",
                                                        "margin": "20px 0 0 0",
                                                        "textAlign": "center"
                                                    }),
                                                        width=6),
                                                dbc.Col(html.H4(
                                                    "Decision Space",
                                                    style={
                                                        "fontWeight": "600",
                                                        "fontFamily":
                                                        "Helvetica",
                                                        "textAlign": "center",
                                                        "margin": "20px 0 0 0"
                                                    }),
                                                        width=6),
                                            ],
                                                    className=
                                                    "mop-custom-container-style"
                                                    # className="my-custom-container-style"
                                                    ),
                                            # id="container-row"
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        dcc.Graph(
                                                            id=
                                                            "mop-objective-graph",
                                                            figure=blank_figure(
                                                            ),
                                                            style={
                                                                'height':
                                                                '42vh'
                                                            }),
                                                        width=6,
                                                    ),
                                                    dbc.Col(
                                                        dcc.Graph(
                                                            id=
                                                            "mop-decision-graph",
                                                            figure=blank_figure(
                                                            ),
                                                            style={
                                                                'height':
                                                                '42vh'
                                                            }),
                                                        width=6,
                                                    ),
                                                    # dbc.Col(
                                                    #     dcc.Dropdown(
                                                    #         id='tests',
                                                    #         options=[
                                                    #             {
                                                    #                 'label':
                                                    #                 'DTLZ1',
                                                    #                 'value':
                                                    #                 'DTLZ1'
                                                    #             },
                                                    #             {
                                                    #                 'label':
                                                    #                 'Aspar',
                                                    #                 'value':
                                                    #                 'Aspar'
                                                    #             },
                                                    #         ],
                                                    #         value='Aspar',
                                                    #         style={
                                                    #             'display': 'none'
                                                    #         })),
                                                ],
                                                className=
                                                "mop-custom-container-style"),
                                            # ]),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Card(
                                                                dbc.CardBody([
                                                                    html.
                                                                    H4("Plot Description",
                                                                       className
                                                                       ="card-title"
                                                                       ),
                                                                    # html.Div([html.H5("Cost Landscape provide valuable insights into the problem's landscape, revealing the challenges and help in identifying potential difficulties, such as discontinuities or multimodality that make MOO hard to solve."),
                                                                    #           html.H6("Test: DTLZ1"),
                                                                    # html.H6("Objective Space: Pareto front plots show the trade-offs between objectives in the objective space"),
                                                                    # html.P("#Objective functions: 2"),
                                                                    # html.P("#Decision variables: 7"),
                                                                    # html.H6("Decision Space:The alternating blue and yellow lines suggest that the Pareto optimal set is not continuous in the decision space but rather consists of discrete region."),
                                                                    # html.P("#Objective functions: 2"),
                                                                    # html.P("#Decision variables: 2"),], className="plot-des")
                                                                ])),
                                                        ],
                                                        className=
                                                        "card-container"),
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
                                                            className=
                                                            "card2-container"),
                                                    # width=6
                                                ],
                                                className="align-cards")
                                            # style={"height":"calc(100vh - 150px)","overflow":"hidden"}
                                        ],
                                        fluid=True,
                                        className="mop-container-style")
                                    #   style={"height":"calc(100vh - 50px)","overflow":"hidden"}
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
                                                                "20px 0 0 0",
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
                                                                "20px 0 0 0"
                                                                # "margin":"50px", "marginLeft":"15rem"
                                                            }),
                                                        width=6)
                                                ],
                                                className=
                                                "my-custom-container-style"),
                                            # id="container-row"
                                            dbc.Row(
                                                [
                                                    dbc.Col(children=[
                                                        dcc.Graph(
                                                            figure=blank_figure(
                                                            ),
                                                            id='graph3',
                                                            style={
                                                                'height':
                                                                '42vh'
                                                            })
                                                    ],
                                                            width=6,
                                                            style={
                                                                'overflow':
                                                                'hidden'
                                                            }),
                                                    dbc.Col(
                                                        html.Div(id="sliders3",
                                                                 style={
                                                                     'height':
                                                                     '42vh'
                                                                 }),
                                                        # className="sliders-container"
                                                        width=6,
                                                        style={
                                                            'overflow':
                                                            'hidden'
                                                        }),
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
                                                            "card-container"),
                                                    # width=6
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
                                                            className=
                                                            "card2-container"),
                                                ],
                                                className="align-cards")
                                            # style={"height":"calc(100vh - 150px)","overflow":"hidden"}
                                        ],
                                        fluid=True)
                                    #   style={"height":"calc(100vh - 50px)","overflow":"hidden"}
                                ]),
                        ],
                        colors={
                            "border": "white",
                            "primary": "red",
                            "background": "#98A5C0"
                        },
                    ),
                    width={'size': 8
                           # 'offset': 0
                           },
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.H5("Plot Control Parameter",
                                    className='plot-class'),
                            html.Hr(),
                            # html.Label("Color by cluster:",
                            #            style={'fontSize': '15px'}),
                            dbc.Checklist(
                                id="use-cluster-toggle",
                                options=[{
                                    "label": "Color by cluster",
                                    "value": 'cluster'
                                }],
                                value=[],
                                inline=True,
                                switch=True,
                                # className="d-flex justify-content-center"
                            ),
                            dcc.Dropdown(id='cluster-dropdown',
                                         options=[],
                                         value=[],
                                         multi=True,
                                         placeholder='Select a cluster',
                                        #  style={'display':'none'},
                                        style={'width':'95%','height':'auto', 'maxHeight':'150px','overflowY':'auto','margin':'0 1px','padding':'2px', 'display':'none'},
                                         ),
                            dbc.Checklist(
                                id="toggle-switch",
                                options=[{"label":"Toggle", "value":'toggle'}],
                                value = [],
                                switch = True,
                                # className='d-flex justify-content-center mt-3'
                                ),
                            dbc.Label("Grid resolution:", style={'fontSize': '15px', 'display':'none'}, id="grid-1"),
                            dbc.Input(id="grid-resolution", type="number", size="sm", min=1, max=100, style={'display':'none'}),
                            html.Br()
                        ],
                        className='control-section',
                        style={'textAlign': 'center', 'display':'flex', 'flexDirection':'column','alignItems':'center'}),
                    width={'size': 2},
                    className='h-75 d-inline-block',
                    style={
                        'height': 'calc(100vh-170px)',
                        'overflow': 'hidden', 'marginLeft':'0px'
                    })
            ],
            # className="content-row"
        ),
    ],
    className="main-container",
    fluid=True)
