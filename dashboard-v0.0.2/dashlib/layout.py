import base64
import json
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import pandas as pd
from .components import blank_figure
# from dashlib.offshore_windfarm.screen3 import get_location_dropdown, create_network_graph
from dashlib.offshore_windfarm.screen3 import get_location_dropdown

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
                                dbc.Col(
                                    dcc.Upload(
                                        id="upload-data",
                                        children=html.Div([
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
                                        ]),
                                        multiple=True,
                                    ), )
                            ]),
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
                                    dbc.Container([
                                        dbc.Row([
                                            dbc.Col([
                                                html.H4(
                                                    "Objective Space",
                                                    style={
                                                        "fontWeight": "600",
                                                        "fontFamily":
                                                        "Helvetica",
                                                        "margin": "20px 0 0 0",
                                                        "textAlign": "center"
                                                    }),
                                                html.Div(
                                                    id=
                                                    'objective-space-content',
                                                    children=[
                                                        html.H6(
                                                            id='obj-help',
                                                            style={
                                                                'textAlign':
                                                                'center'
                                                            }),
                                                        dcc.Loading(
                                                            id='loading-graph',
                                                            children=[
                                                                dcc.Graph(
                                                                    figure=
                                                                    blank_figure(
                                                                    ),
                                                                    id='graph1',
                                                                    style={
                                                                        'height':
                                                                        '35vh'
                                                                    })
                                                            ],
                                                            target_components={
                                                                'graph1':
                                                                ['figure']
                                                            })
                                                    ])
                                            ],
                                                    width=6,
                                                    id='graph-col'),
                                            dbc.Col([
                                                html.H4(
                                                    "Decision Space",
                                                    style={
                                                        "fontWeight": "600",
                                                        "fontFamily":
                                                        "Helvetica",
                                                        "textAlign": "center",
                                                        "margin": "20px 0 0 0"
                                                    }),
                                                html.H6(id='dec-help',
                                                        style={
                                                            'textAlign':
                                                            'center'
                                                        }),
                                                html.Div(
                                                    id='decision-space-content',
                                                    children=[
                                                        html.Div(id="sliders")
                                                    ])
                                            ],
                                                    width=6,
                                                    id="radar-col"),
                                            dbc.Alert(
                                                'No data exists reflecting that change',
                                                id='no-data-alert',
                                                color='danger',
                                                is_open=False,
                                                dismissable=True,
                                                duration=5000,
                                                style={
                                                    'position': 'absolute',
                                                    'top': '15%',
                                                    'left': '50%',
                                                    'zIndex': 999
                                                })
                                        ],
                                                className=
                                                "my-custom-container-style"),
                                        dbc.Row([
                                            dbc.Col([
                                                dbc.Card(
                                                    dbc.CardBody([
                                                        html.H4(
                                                            "Plot Description",
                                                            className=
                                                            "card-title")
                                                    ],
                                                                 style={
                                                                     'height':
                                                                     '27vh'
                                                                 }))
                                            ],
                                                    className="card2-container"
                                                    ),
                                            dbc.Col([
                                                dbc.Card(
                                                    dbc.CardBody([
                                                        html.
                                                        H4("Fairness Index (Future Capability)",
                                                           className=
                                                           "card-title2")
                                                    ],
                                                                 style={
                                                                     'height':
                                                                     '27vh'
                                                                 }))
                                            ],
                                                    className="card2-container"
                                                    ),
                                        ],
                                                className="align-cards")
                                    ],
                                                  fluid=True,
                                                  className=
                                                  'dbc-container-style')
                                ]),
                            dcc.Tab(
                                label='MOP Structure',
                                value='tab-2-example-graph',
                                className='custom-tab',
                                selected_className='custom-tab--selected',
                                children=[
                                    dbc.Container([
                                        dbc.Row([
                                            dbc.Col(html.H4(
                                                "Objective Space",
                                                style={
                                                    "fontWeight": "600",
                                                    "fontFamily": "Helvetica",
                                                    "margin": "20px 0 0 0",
                                                    "textAlign": "center"
                                                }),
                                                    width=6),
                                            dbc.Col(html.H4(
                                                "Decision Space",
                                                style={
                                                    "fontWeight": "600",
                                                    "fontFamily": "Helvetica",
                                                    "textAlign": "center",
                                                    "margin": "20px 0 0 0"
                                                }),
                                                    width=6),
                                        ],
                                                className=
                                                "mop-custom-container-style"),
                                        dbc.Row([
                                            dbc.Col(
                                                dcc.Graph(
                                                    id="mop-objective-graph",
                                                    figure=blank_figure(),
                                                    style={'height': '42vh'}),
                                                width=6,
                                            ),
                                            dbc.Col(
                                                dcc.Graph(
                                                    id="mop-decision-graph",
                                                    figure=blank_figure(),
                                                    style={'height': '42vh'}),
                                                width=6,
                                            ),
                                        ],
                                                className=
                                                "mop-custom-container-style"),
                                        dbc.Row([
                                            dbc.Col([
                                                dbc.Card(
                                                    dbc.CardBody([
                                                        html.H4(
                                                            "Plot Description",
                                                            className=
                                                            "card-title"),
                                                    ],
                                                                 style={
                                                                     'height':
                                                                     '27vh'
                                                                 })),
                                            ],
                                                    className="card2-container"
                                                    ),
                                            dbc.Col([
                                                dbc.Card(
                                                    dbc.CardBody([
                                                        html.
                                                        H4("Fairness Index (Future Capability)",
                                                           className=
                                                           "card-title2")
                                                    ],
                                                                 style={
                                                                     'height':
                                                                     '27vh'
                                                                 })),
                                            ],
                                                    className="card2-container"
                                                    ),
                                        ],
                                                className="align-cards")
                                    ],
                                                  fluid=True,
                                                  className=
                                                  "mop-container-style")
                                ]),
                            dcc.Tab(
                                label='Offshore Windfarm UseCase',
                                value='tab-3-example-graph',
                                className='custom-tab',
                                selected_className='custom-tab--selected',
                                children=[
                                    dbc.Container(
                                        [
                                            # dbc.Row(
                                            #     [
                                            #         # dbc.Col(dcc.Graph(id ="network-graph",
                                            #                         #   figure=create_network_graph()
                                            #             dbc.Col(style={
                                            #                     "fontWeight":
                                            #                     "600",
                                            #                     "fontFamily":
                                            #                     "Helvetica",
                                            #                     "margin":
                                            #                     "20px 0 0 0",
                                            #                     # "textAlign":
                                            #                     # "center"
                                            #                 },
                                            #             width=4),
                                            #         dbc.Col(
                                            #             html.H4(
                                            #                 "Objective Space",
                                            #                 style={
                                            #                     "fontWeight":
                                            #                     "400",
                                            #                     "fontFamily":
                                            #                     "Helvetica",
                                            #                     "margin":
                                            #                     "20px 0 0 0",
                                            #                     "textAlign":
                                            #                     "center"
                                            #                 }),
                                            #             width=4),
                                            #         dbc.Col(
                                            #             html.H4(
                                            #                 "Decision Space",
                                            #                 style={
                                            #                     "fontWeight":
                                            #                     "400",
                                            #                     "fontFamily":
                                            #                     "Helvetica",
                                            #                     "textAlign":
                                            #                     "center",
                                            #                     "margin":
                                            #                     "20px 0 0 0"
                                            #                 }),
                                            #             width=4)
                                            #     ],
                                            #     className=
                                            #     "my-custom-container-style"),
                                            dbc.Row(
                                                [
                                                    dbc.Col(dcc.Graph(
                                                        id='graph4',figure=blank_figure(),config={'displayModeBar' : False},
                                                        style={'height': '37vh'}),
                                                            width={
                                                                'size': 5,
                                                                'order': 1
                                                            },
                                                            style={
                                                                'overflow':
                                                                'hidden', "paddingRight": "10px",
                                                            }),
                                                    dbc.Col(
                                                        html.Div([
                                                            html.
                                                            H4("Objective Space",
                                                               style={
                                                                   "textAlign":
                                                                   "center",
                                                                   "marginTop":
                                                                   "10px","fontWeight":
                                                                "700","fontFamily":
                                                                "Helvetica",
                                                                  
                                                               }),
                                                            dcc.Graph(
                                                                id='graph3',
                                                                figure=
                                                                blank_figure(),
                                                                style={
                                                                    'height':
                                                                    '25vh',
                                                                })
                                                        ]),
                                                        # width=4,
                                                        width={
                                                            'size': 3,
                                                            'order': 2
                                                        },
                                                        style={
                                                            'overflow':
                                                            'hidden', "textAlign":"center"
                                                        }),
                                                    dbc.Col(html.Div([
                                                        html.H4(
                                                            "Decision Space",
                                                            style={
                                                                "textAlign":
                                                                "center",
                                                                "marginTop":
                                                                "10px","fontWeight":
                                                                "700","fontFamily":
                                                                "Helvetica",
                                                            }),
                                                        html.Div(id="sliders3",
                                                                 style={
                                                                     'height':
                                                                     '25vh'
                                                                 })
                                                    ]),
                                                            width={
                                                                'size': 4,
                                                                'order': 3
                                                            },
                                                            style={
                                                                'overflow':
                                                                'hidden',"paddingLeft":"10px"
                                                            }),
                                                ],
                                                className="offshore"),
                                            dbc.Row([
                                                dbc.Col([
                                                    dbc.Card(
                                                        dbc.CardBody([
                                                            html.
                                                            H4("Wind Speed Timeseries",
                                                               className=
                                                               "card-title"),
                                                            dcc.Graph(
                                                                id=
                                                                "time-series-graph",
                                                                style={
                                                                    'height':
                                                                    '35vh'
                                                                }),
                                                        ]))
                                                ],
                                                        className=
                                                        "card3-container"),
                                                dbc.Col([
                                                    dbc.Card(
                                                        dbc.CardBody([
                                                            html.H4(
                                                                "LMP",
                                                                className=
                                                                "card-title2"),
                                                            dcc.Graph(
                                                                id=
                                                                "fairness-index-graph",
                                                                style={
                                                                    'height':
                                                                    '35vh'
                                                                }),
                                                        ]))
                                                ],
                                                        className=
                                                        "card3-container"),
                                            ],
                                                    className="align3-cards")
                                        ],
                                        fluid=True,
                                        className='dbc-container3-style')
                                ]),
                        ],
                        colors={
                            "border": "white",
                            "primary": "red",
                            "background": "#98A5C0"
                        },
                    ),
                    width={'size': 8},
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.H5("Plot Control Parameter",
                                    className='plot-class'),
                            html.Hr(style={
                                'borderColor': 'black',
                                'width': '100%'
                            }),
                            dbc.Checklist(
                                id="use-cluster-toggle",
                                options=[{
                                    "label": "Color by cluster",
                                    "value": 'cluster'
                                }],
                                value=[],
                                inline=True,
                                switch=True,
                            ),
                            dcc.Dropdown(
                                id='cluster-dropdown',
                                options=[],
                                value=[],
                                multi=True,
                                placeholder='Select a cluster',
                                style={
                                    'width': '95%',
                                    'height': 'auto',
                                    'maxHeight': '150px',
                                    'overflowY': 'auto',
                                    'margin': '0 1px',
                                    'padding': '2px',
                                    'display': 'none'
                                },
                            ),
                            dbc.Label("Grid resolution:",
                                      style={
                                          'fontSize': '15px',
                                          'display': 'none'
                                      },
                                      id="grid-1"),
                            dbc.Input(id="grid-resolution",
                                      type="number",
                                      size="sm",
                                      min=1,
                                      max=100,
                                      style={'display': 'none'}),
                            html.Br(),
                            html.Div([
                                html.Div(
                                    [
                                        dbc.Label(
                                            "HYPERPARAMETERS",
                                            style={
                                                'fontSize': "40px",
                                                'display': 'none'
                                                #   'textAlign': 'left',
                                                #   'alignItems': 'left',
                                                #   'left':'0px'
                                            },
                                            id="grid-2"),
                                        html.Div(id="hyperparameter-dropdowns",
                                                 style={'display': 'none'})
                                    ],
                                    style={
                                        'textAlign': 'left',
                                        'alignItems': 'left'
                                    }),
                                html.Div(
                                    [
                                        dbc.Label("Location",
                                                  style={
                                                      "fontSize": "15px",
                                                      'left': '0px',
                                                      'textAlign': 'left',
                                                      'marginTop': '4px'
                                                  }),
                                        get_location_dropdown()
                                    ],
                                    style={
                                        'textAlign': 'left',
                                        'width': '150%',
                                        'display': 'none'
                                    },
                                    id="location"),
                                # dbc.Label("Input-parameters:",
                                #           style={
                                #               'fontSize': '15px',
                                #               'display': 'none'
                                #           },
                                #           id="grid-2"),
                                # html.Label("Location",style={'display':'none'}),
                                # html.Div(get_location_dropdown(),style={'display':'none'}),
                            ])
                        ],
                        className='control-section',
                        style={
                            # 'textAlign': 'center',
                            'display': 'flex',
                            'flexDirection': 'column',
                            # 'alignItems': 'center'
                        }),
                    width={'size': 2},
                    className='h-75 d-inline-block',
                    style={
                        'height': 'calc(100vh-170px)',
                        'overflow': 'hidden',
                        'marginLeft': '0px'
                    })
            ], ),
    ],
    className="main-container",
    fluid=True)
