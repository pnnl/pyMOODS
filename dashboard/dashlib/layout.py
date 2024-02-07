from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from .components import blank_figure

interface_layout = html.Div([
    dcc.Store(id="stored-df"),
    # html.Div(id='placeholder'),
    html.H1(
        children=
        "pyMOODS: Multi-Objective Optimization Decision Support System",
        style={
            "fontWeight": "400",
            "textAlign": "center",
            "marginTop": "1rem",
        },
    ),
    dcc.Upload(
        id="upload-data",
        children=html.Div([
            html.Div(html.H3("Data Upload")),
            html.Hr(),
            dbc.Button('Upload File', outline=True, color="dark", size="lg")
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
            "fontFamily":"Helvetica",
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
                            dbc.Row([
                                dbc.Col(),
                                dbc.Col(html.H4("Objective Space",
                                                style={
                                                    "fontWeight": "550",
                                                    "borderTop": "120px",
                                                    "paddingTop": "40px",
                                                    'fontFamily':"Helvetica"
                                                }),
                                        width=5),
                                dbc.Col(html.H4("Decision Space",
                                                style={
                                                    "fontWeight": "600",
                                                    "borderTop": "120px",
                                                    "paddingTop": "40px",
                                                    'fontFamily':"Helvetica",
                                                    'marginLeft':'70px'
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
                                            dcc.Graph(figure=blank_figure(), style={"backgroundColor":"transparent"},
                                                      id='graph1')
                                        ]),
                                    dbc.Col(html.Div(id="sliders")),
                                ],
                                className="my-custom-container-style"
                                ),
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
