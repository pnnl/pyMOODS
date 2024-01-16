import base64
import datetime
import io
from pymoo.problems import get_problem
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
#from dash_bootstrap_templates import load_figure_template
#load_figure_template('LUX')


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.LUX],
    suppress_callback_exceptions=True,
)

server = app.server

app.layout = html.Div([
    dcc.Store(id="stored-df"),
    dbc.Row(html.H1(
        children="Multi-Objective Optimization Decision Support System",
        style={
            "fontFamily": "Open Sans",
            "fontWeight": "semibold",
            "textAlign": "center",
            "padding-top":"1rem",
            # "textDecoration":"underline",
            "color":"MidnightBlue",
            #"backgroundColor": "green",
        },
    ), ),
    dbc.Row([
        dbc.Col(),
        dbc.Col(html.H3("Solution Dominance", style={
            "fontFamily": "Gill Sans",
            "fontWeight": "550",
            "border-top": "120px",
            "padding-top":"40px",
            "left":"50px",
            "color":"Brown",
            #"backgroundColor" :"Darkgrey",
            }), width=10),
    ]),
    dbc.Row([
            dbc.Col(dcc.Upload(
            id="upload-data",
            children=html.Div([
                html.Div(html.H3("Data Upload"), style={"left" : "1rem"}),
                html.Hr(),
                dbc.Button(
                    'Upload File',
                    outline=True,
                    color="primary",
                )], 
                ),
            style=
            {
                'border-top': '200px',
                "position": "fixed",
                "top": 0,
                "bottom": 0,
                #"width": "14rem",
                "padding": "8rem 1rem 50rem 1.5rem",
                #"background-color": "#f8f9fa",
                "background-color":"#ced5dc"
            },
            multiple=True,),width=2),
            dbc.Col(html.Div(id="graph-container",
                        style={
                            #  'display': 'inline-block',
                            #  'width': '70%',
                            #  'left': '100px',
                            # 'fontSize': '18',
                            # 'font-family': 'Arial',
                            # 'backgroundColor': '#ffffff',
                            # 'padding-top':'-20'
                            'size': 'md',
                         }
                         ), width=6),
            
            dbc.Col(html.Div(
                    [
                        html.Div([
                            html.Label([
                                "x1",
                            ], ),
                            dcc.Slider(min=0, max=1, step=0.1, id="slider1")
                        ], ),
                        html.Div([
                            html.Label([
                                "x2",
                            ], ),
                            dcc.Slider(min=0, max=1, step=0.1, id="slider2")
                        ], ),
                        html.Div([
                            html.Label([
                                "x3",
                            ], ),
                            dcc.Slider(min=0, max=1, step=0.1, id="slider3")
                        ], ),
                        html.Div([
                            html.Label([
                                "x4",
                            ], ),
                            dcc.Slider(min=0, max=1, step=0.1, id="slider4")
                        ], )
                    ],
                    style={
                        # 'display': 'inline-block',
                        # 'width': '50%',
                        'padding-top': '10%',
                        # 'float': 'right',
                        'fontSize': '18',
                        'font-family': 'Arial',
                        'font-weight':'400',
                        #'backgroundColor': '#ffffff',
                        'paper_bgcolor':'rgb(0,0,0,0)',
                        'plot_bgcolor':'rgba(0,0,0,0)',
                    }
                    ), width=4),
        ]),
    dbc.Row([
        dbc.Col(),
        dbc.Col(html.H5("Objective Space", style={
            "fontFamily": "Gill Sans",
            "fontWeight": "550",
            "border-top": "120px",
            "padding-top":"40px",
            "left":"200px",
            "color":"Black",
            #"textTransform":"capitalize",
            })),
        dbc.Col(html.H5("Decision Space", style={
            "fontFamily": "Gill Sans",
            "fontWeight": "550",
            "border-top": "120px",
            "padding-top":"40px",
            "left":"400px",
            "textAlign" : "center",
            "color":"Black",
            })),
    ]),
    
    dbc.Row([
        dbc.Col(),
        dbc.Col(html.H3("Quality of Pareto Front", style={
            "fontFamily": "Gill Sans",
            "fontWeight": "550",
            "border-top": "120px",
            "padding-top":"40px",
            "left":"50px",
            "color":"Brown",
            }), width=10),
    ]),
    
    dbc.Row([
        dbc.Col(),
        dbc.Col(html.Img(src="data:image/png;base64,{}".format(base64.b64encode(open('assets/ParetoF1.png','rb').read()).decode())), 
                         style={
             #'size' : 'sm',
             'width' : '45%',
            'height':'40%'
            }, 
                       # width=5
                         ),
        dbc.Col(html.Img(src="data:image/png;base64,{}".format(base64.b64encode(open('assets/ParetoF2.png','rb').read()).decode())), 
                 style={
            # "border-top": "120px",
            # "padding-top":"40px",
            # "left":"400px",
            # "textAlign" : "center",
            #'size':'sm'
            'width' : '40%',
            'height':'40%'
            }, 
             # width=5
                ),
    ]),
    
    dbc.Row([
        dbc.Col(),
        dbc.Col(html.H5("Pareto Front 1", style={
            "fontFamily": "Gill Sans",
            "fontWeight": "550",
            "border-top": "120px",
            "padding-top":"40px",
            "left":"200px",
            "color":"Black",
            })),
        dbc.Col(html.H5("Pareto Front 2", style={
            "fontFamily": "Gill Sans",
            "fontWeight": "550",
            "border-top": "120px",
            "padding-top":"40px",
            "left":"400px",
            "textAlign" : "center",
            "color":"Black",
            })),
    ]),
    
    dbc.Row([
        dbc.Col(),
        dbc.Col(html.H3("Model Reasoning", style={
            "fontFamily": "Gill Sans",
            "fontWeight": "550",
            "border-top": "120px",
            "padding-top":"40px",
            "left":"50px",
            "color":"Brown",
            }), width=10),
    ]),
     
     dbc.Row([
        dbc.Col(),
        dbc.Col(html.Img(src="data:image/png;base64,{}".format(base64.b64encode(open('assets/Model1.png','rb').read()).decode())), style={
            # "border-top": "120px",
            # "padding-top":"40px",
            # "left":"200px",
            #'size':'sm'
            'width' : '45%',
            'height':'40%',
            }, 
                #width=5
                ),
        dbc.Col(html.Img(src="data:image/png;base64,{}".format(base64.b64encode(open('assets/Model2.png','rb').read()).decode())), style={
            # "border-top": "120px",
            # "padding-top":"40px",
            # "left":"400px",
            # "textAlign"' : "center",
            # 'size':'sm'
            'width' : '40%',
            'height':'40%'
            },
                #width=5
                ),
    ]),
     dbc.Row([
        dbc.Col(),
        dbc.Col(html.H5("Model 1", style={
            "fontFamily": "Gill Sans",
            "fontWeight": "550",
            "border-top": "120px",
            "padding-top":"40px",
            "left":"200px",
            "color":"Black",
            })),
        dbc.Col(html.H5("Model 2", style={
            "fontFamily": "Gill Sans",
            "fontWeight": "550",
            "border-top": "120px",
            "padding-top":"40px",
            "left":"400px",
            "textAlign" : "center",
            "color":"Black",
            })),
    ]),
     
    ], style={"background-color": "#f8f9fa"})

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
    Output("graph-container", "children", allow_duplicate=True),
    Output("stored-df", "data"),
    [Input("upload-data", "contents"),
     Input("upload-data", "filename")],
    prevent_initial_call=True)
def update_output(contents, filename):
    if contents is not None:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)
        fig = gen_graph(df)
        graph = dcc.Graph(figure=fig, id='graph1')
        return graph, df.to_dict('records')


def gen_graph(df):
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
                height=350
            ),
                 #layout=go.Layout(width=20, height=20)
                )
            fig.update_xaxes(showgrid=False, linecolor='black')
            fig.update_yaxes(showgrid=False, linecolor='black')
            fig.update_layout(
                font=dict(
                family="Times New Roman",
                color="black",
                size= 18),
                margin=dict(l=10, r=20, t=20, b=20),
                paper_bgcolor='rgb(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
            )
            #graph = dcc.Graph(figure=fig, id='graph1')

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
            #graph = dcc.Graph(figure=fig, id='graph1')

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

        # graph = dcc.Graph(figure=fig, id='graph1')

    return fig


@app.callback(Output('slider1', 'value'), Output('slider2', 'value'),
              Output('slider3', 'value'), Output('slider4', 'value'),
              Input('graph1', 'clickData'), State('stored-df', 'data'))
def slider_output(graph_point, my_data):
    if graph_point:
        df = pd.DataFrame(my_data)
        #print(df.head())
        
        f1_point = graph_point['points'][0]['x']
        f2_point = graph_point['points'][0]['y']
        dff = df[(df.f1 == f1_point) & (df.f2 == f2_point)]
        return dff.x1.values[0], dff.x2.values[0], dff.x3.values[
            0], dff.x4.values[0]
    else:
        return no_update


@app.callback(Output('graph1', "figure"), [
    Input('slider1', 'value'),
    Input('slider2', 'value'),
    Input('slider3', 'value'),
    Input('slider4', 'value')
], State('graph1', "figure"), State('stored-df', 'data'))

def pareto_front(x1_val, x2_val, x3_val, x4_val, fig, data):
    DTLZ2 = get_problem("dtlz2", n_var=4, n_obj=2)
    dff = DTLZ2.evaluate(np.array([x1_val, x2_val, x3_val, x4_val]))
    print(dff)
    
    fig = gen_graph(pd.DataFrame.from_dict(data))

    #print(fig["traces"])
    fig.add_scatter(x=[dff[0]], y=[dff[1]], marker=dict(color='red', size=10))
    fig.update_layout(showlegend=False)
    # fig.update_xaxes(showgrid=False)
    #fig.update_yaxes(showgrid=False)
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
