import json
import pandas as pd
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
#from pymoo.problems import get_problem

from dashlib.layout import interface_layout
from dashlib.components import gen_graph
from data.parser import parse_data
from logger.custom import NumpyEncoder

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
)

divFlex = {'display': 'flex', 'padding': "0.5rem", 'width': '38%'}
labelFlex = {'flexShrink': 0, 'fontFamily':"Helvetica",}

app.layout = interface_layout


@app.callback(Output({
    "type": "ds-sliders",
    "index": ALL
}, "value"), Input('graph1', 'clickData'), [
    State('stored-df', 'data'),
    State({
        "type": "ds-sliders",
        "index": ALL
    }, "id")
])
def slider_output(click_data, my_data, slider_ids):
    # FIXME: Get from slider ids
    # decision_variables = ['x1', 'x2', 'x3', 'x4']
    if click_data and my_data:
        df = pd.DataFrame(my_data)

        f1_point = click_data['points'][0]['x']
        f2_point = click_data['points'][0]['y']
        dff = df[(df.f1 == f1_point) & (df.f2 == f2_point)]
        if not dff.empty and len(slider_ids) > 0:
            decision_variables = [
                id['index'].split('-')[1] for id in slider_ids
            ]

            if pd.Series(decision_variables).isin(dff.columns).all():
                return list(dff[decision_variables].values[0])

    return [0 for _ in slider_ids]


@app.callback(Output("graph1", "figure", allow_duplicate=True),
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
        df, decision_variables, objective_functions = parse_data(
            contents, filename)

        if df is not None:
            # Save categorized data to "categorized_data.json"
            categorized_data = {
                "Decision Variables": {
                    key: {
                        "values": value,
                        "min": 0,
                        "max": 1
                    }
                    for key, value in decision_variables.items()
                },
                "Objective Functions": {
                    key: value
                    for key, value in objective_functions.items()
                },
            }
            with open("categorized_data.json", "w") as outfile:
                json.dump(categorized_data,
                          outfile,
                          cls=NumpyEncoder,
                          indent=4)

            fig = gen_graph(df)
            sliders = [
                html.Div(
                    [
                        # html.Div(children=[
                        html.Div(col, style=labelFlex),
                        dcc.Slider(
                            id={
                                'type': 'ds-sliders',
                                'index': f'slider-{col}'
                            },
                            min=min_val,
                            max=max_val,
                            step=0.25,
                            marks={
                                i: f'{i: .2f}'
                                for i in np.arange(min_val, max_val +
                                                   0.1, 0.25)
                            },
                            tooltip={
                                "placement": "bottom",
                                "always_visible": True
                            }),
                        # ],
                        #  style=divFlex),
                    ], )
                for col, (min_val,
                          max_val) in zip(decision_variables.keys(), [(0, 1)] *
                                          len(decision_variables))
            ]

            # generate_slider_callback([
            #     Output(f'slider-{col}', 'value')
            #     for col in decision_variables.keys()
            # ], list(decision_variables.keys()))

            return fig, df.to_dict('records'), sliders

    return dash.no_update, [], []


# @app.callback(Output('graph1', "figure"),
#               [Input({
#                   "type": "ds-sliders",
#                   "index": ALL
#               }, "value")], State('graph1', "figure"),
#               State('stored-df', 'data'))
# def pareto_front(slider_values, fig, data):
#     if data is None:
#         return fig
#     n_var = len(slider_values)
#     n_obj = len(data[0]) - n_var
#     DTLZ2 = get_problem("dtlz2", n_var=n_var, n_obj=n_obj)
#     dff = DTLZ2.evaluate(np.array(slider_values))
#     print(dff)
#     fig = gen_graph(pd.DataFrame.from_dict(data))
#     fig.add_scatter(x=[dff[0]], y=[dff[1]], marker=dict(color='blue', size=30, symbol='star'))
#     fig.update_layout(showlegend=False)
#     fig.update_traces(hovertemplate='<b>f1</b>: %{x}' +
#                     '<br><b>f2</b>: %{y}<extra></extra>',
#                     hoverlabel=dict(font_size=22))
#     return fig


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
    app.run_server(debug=True, host="0.0.0.0", port=5000)
