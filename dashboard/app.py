import json
import pandas as pd
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
# from pymoo.problems import get_problem

from dashlib.layout import interface_layout
from dashlib.components import gen_graph
from data.parser import parse_data
from logger.custom import NumpyEncoder

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
)

app.layout = interface_layout

@app.callback(Output({"type": "ds-sliders", "index": ALL}, "value"),
inputs= Input('graph1', 'clickData'),
state= State('stored-df', 'data'))
def slider_output(click_data, my_data):
    # FIXME: Get from slider ids 
    decision_variables = ['x1', 'x2', 'x3', 'x4']
    if click_data and my_data:
        df = pd.DataFrame(my_data)
        
        f1_point = click_data['points'][0]['x']
        f2_point = click_data['points'][0]['y']
        dff = df[(df.f1 == f1_point) & (df.f2 == f2_point)]
        if not dff.empty and pd.Series(decision_variables).isin(dff.columns).all():
            return list(dff[decision_variables].values[0])
    
    return [0 for dv in decision_variables]

@app.callback(Output("graph1", "figure"),
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
            sliders = [
                html.Div([
                    html.Label(col,
                               style={
                                   "fontSize": "27px",
                                   "fontWeight": "bold"
                               }),
                    dcc.Slider(
                        id={'type': 'ds-sliders', 'index': f'slider-{col}'},
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
            # output_list=[]
            # d_v = []
            # for col in decision_variables.keys():
            #     output_list.append(Output(f'slider-{col}', 'value'))
            #     d_v.append(col)
            #     print("H")
            # print(df)
            # generate_slider_callback(output_list, d_v)
            return fig, df.to_dict('records'), sliders
        
    return dash.no_update, [], []

# @app.callback(Output("placeholder", "children"),
# inputs= Input('graph1', 'clickData'),
# state= State('stored-df', 'data'))
# def slider_output(click_data, my_data):
#     print("Hello")
#     if click_data and my_data:
#         df = pd.DataFrame(my_data)
        
#         f1_point = click_data['points'][0]['x']
#         f2_point = click_data['points'][0]['y']
#         dff = df[(df.f1 == f1_point) & (df.f2 == f2_point)]
#         decision_variables = ['x1', 'x2', 'x3', 'x4']
#         if not dff.empty:# and decision_variables in dff.columns:
#             # return dff[decision_variables].values[0]
#             return "Hello"
        
#     return "Bye"

# @app.callback(Output('graph1', "figure"), [
#     Input('slider1', 'value'),
#     Input('slider2', 'value'),
#     Input('slider3', 'value'),
#     Input('slider4', 'value')
# ], State('graph1', "figure"), State('stored-df', 'data'))
# def pareto_front(x1_val, x2_val, x3_val, x4_val, fig, data):
#     DTLZ2 = get_problem("dtlz2", n_var=4, n_obj=2)
#     dff = DTLZ2.evaluate(np.array([x1_val, x2_val, x3_val, x4_val]))
#     print(dff)
#     fig = gen_graph(pd.DataFrame.from_dict(data))
#     fig.add_scatter(x=[dff[0]], y=[dff[1]], marker=dict(color='red', size=12))
#     fig.update_layout(showlegend=False)
#     return fig


if __name__ == "__main__":
    app.run_server(debug=True)