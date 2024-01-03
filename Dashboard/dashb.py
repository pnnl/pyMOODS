import base64
import datetime
import io

import dash
from dash.dependencies import Input, Output, State
from dash import Dash, dcc, html, Patch, no_update
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt
# from matplotlib import figure
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)

server = app.server

app.layout = html.Div([
    dcc.Store(id="stored-df"),
    html.H1(
        children="Multi-Objective Optimization Visualization",
        style={
            "fontFamily": "Gill Sans",
            "fontWeight": "400",
            "textAlign": "center",
        },
    ),
    dcc.Upload(
        id="upload-data",
        children=html.Div(["Drag and Drop or ",
                           html.A("Select Files")]),
        style={
            "width": "100",
            "height": "60px",
            "lineHeight": "60px",
            "borderWidth": "1px",
            "borderStyle": "dashed",
            "borderRadius": "5px",
            "textAlign": "center",
            "margin": "10px",
        },
        # Allow multiple files to be uploaded
        multiple=True,
    ),
    html.Div([
        html.Div([
            html.Div(id="graph-container",
                     style={
                         'display': 'inline-block',
                         'width': '60%',
                     }),
            html.Div(
                [
                    html.Div([
                        html.Label([
                            "x1",
                        ], ),
                        dcc.Slider(min=0, max=1, step=0.1, id="slider1")
                    ],
                    ),
                    html.Div([
                        html.Label([
                            "x2",
                        ], ),
                        dcc.Slider(min=0, max=1, step=0.1, id="slider2")
                    ],
                             ),
                    html.Div([
                        html.Label([
                            "x3",
                        ], ),
                        dcc.Slider(min=0, max=1, step=0.1, id="slider3")
                    ],
                             ),
                    html.Div(
                        [
                            html.Label([
                                "x4",
                            ], ),
                            dcc.Slider(min=0, max=1, step=0.1, id="slider4")
                        ],
                        )
                ],
                style={
                    'display': 'inline-block',
                    'width': '40%',
                    'padding-top': '4%',
                    'float': 'right',
                    'fontSize': '14',
                    'font-family': 'Arial',
                    'backgroundColor': '#ffffff'
                })
        ] )
    ])
])


# File upload function
def parse_data(contents, filename):
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)
    try:
        if "csv" in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        elif "xls" in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div(["There was an error processing this file."])
    return df


@app.callback(
    Output("graph-container", "children"),
    Output("stored-df", "data"),
    [Input("upload-data", "contents"),
     Input("upload-data", "filename")],
    prevent_initial_call=True
)
def update_output(contents, filename):
    if contents is not None:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)

        cols1 = ["f1", "f2"]
        cols2 = ["f1", "f2", "f3"]
        cols3 = ["f1", "f2", "f3", "f4"]

        for c in df.columns:
            if c in cols1:
                fig = go.Figure(px.scatter(
                    df,
                    x=df["f1"],
                    y=df["f2"],
                    labels={
                        "df[f1]": "f1",
                        "df[f2]": "f2",
                    },
                ),
                layout=go.Layout(width=50, height=50))
                graph = dcc.Graph(figure=fig, id='graph1')

            elif c in cols2:
                fig = go.Figure(
                    px.scatter_3d(
                        df,
                        x=df["f1"],
                        y=df["f2"],
                        z=df["f3"],
                        labels={
                            "df[f1]": "f1",
                            "df[f2]": "f2",
                            "df[f3]": "f3",
                        },
                    ))
                graph = dcc.Graph(figure=fig, id='graph1')

            elif c in cols3:
                fig = go.Figure(
                    px.scatter_3d(
                        df,
                        x=df["f1"],
                        y=df["f2"],
                        z=df["f3"],
                        color=df["f4"],
                        labels={
                            "df[f1]": "f1",
                            "df[f2]": "f2",
                            "df[f3]": "f3",
                            "df[f4]": "f4",
                        },
                    ))

                graph = dcc.Graph(figure=fig, id='graph1')

        return graph, df.to_dict('records')

@app.callback(
    Output('slider1','value'),
    Output('slider2','value'),
    Output('slider3', 'value'),
    Output('slider4', 'value'),
    Input('graph1','clickData'),
    State('stored-df','data')
)

def slider_output(graph_point, my_data):
    if graph_point:
        df = pd.DataFrame(my_data)
        #print(df.head())
        f1_point = graph_point['points'][0]['x']
        f2_point = graph_point['points'][0]['y']
        dff = df[(df.f1==f1_point) & (df.f2==f2_point)]
        return dff.x1.values[0],dff.x2.values[0],dff.x3.values[0],dff.x4.values[0]
    else:
        return no_update

if __name__ == "__main__":
    app.run_server(debug=True)