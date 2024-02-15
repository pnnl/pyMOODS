import base64
import json
import pandas as pd
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
from pymoo.problems import get_problem
import plotly.graph_objs as go
from dashlib.layout import interface_layout
from dashlib.components import gen_graph
from data.parser import parse_data
from logger.custom import NumpyEncoder

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
)

divFlex = {'display': 'flex', 'padding': "0.2rem", 'width': '38%'}
labelFlex = {
    'flexShrink': 0,
    'fontFamily': "Helvetica",
}

app.layout = interface_layout

app.layout = html.Div([
    dcc.Store(id="slider-values-store", data={}),
    dcc.Store(id="slider-change-status", data={}),
    interface_layout
])


@app.callback(
    Output("summary-table", 'style'), Output("summary-table", 'children'),
    [Input('upload-data', 'contents'),
     Input('upload-data', 'filename')])
def update_summary(contents, filename):
    if contents is None:
        return {'display': 'none'}, []

    #parse the uploaded file
    content_type, content_string = contents[0].split(',')
    decoded = base64.b64decode(content_string)
    file = json.loads(decoded)

    df = pd.DataFrame(file)

    decision_variables = [col for col in df.columns if col.startswith('x')]
    objective_functions = [col for col in df.columns if col.startswith('f')]
    size = len(df)

    # summary_table = html.Table([
    #     html.Td(html.H4("SUMMARY"), style={'textAlign':'center', 'paddingLeft':'3.5rem'}),
    #     html.Tr([
    #         html.Td(html.H5("#Decision variables:")),
    #         html.Td(html.H5(len(decision_variables)), style={'color': 'blue'})
    #     ]),
    #     html.Tr([
    #         html.Td(html.H5("#Objective Variables:")),
    #         html.Td(html.H5(len(objective_functions)), style={'color': 'blue'})
    #     ]),
    #     html.Tr([
    #         html.Td(html.H5("Size of Pareto Front:")),
    #         html.Td(html.H5(size), style={'color': 'blue'})
    #     ]),
    # ])
    # return summary_table
    summary_table = html.Table([
        html.Tr([
            html.Td(html.H4("SUMMARY"),
                    style={
                        'textAlign': 'center',
                        'paddingLeft': '3.5rem'
                    }),
            html.Td(),
            html.Td(),
        ]),
        html.Tr([
            html.Td(html.H5("#Decision variables:")),
            html.Td(html.H5(len(decision_variables)), style={'color': 'blue'})
        ]),
        html.Tr([
            html.Td(html.H5("#Objective Variables:")),
            html.Td(html.H5(len(objective_functions)), style={'color': 'blue'})
        ]),
        html.Tr([
            html.Td(html.H5("Size of Pareto Front:")),
            html.Td(html.H5(size), style={'color': 'blue'})
        ]),
    ])

    return {
        'margin': '10rem 4rem auto 4.2rem',
        'fontWeight': '500',
        'borderRadius': '10px',
        'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.8)',
        'padding': '1.7rem',
        'fontFamily': 'Arial, Helvetica, sans-serif',
        'textAlign': 'center',
        'width': '69%'
    }, summary_table





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
                        html.Div(
                            col, style=labelFlex, className="slider-label"),
                        dcc.Slider(
                            id={
                                'type': 'ds-sliders',
                                'index': f'slider-{col}'
                            },
                            min=min_val,
                            max=max_val,
                            step=round((max_val-min_val)/4,2),
                            # step=0.001,
                            marks={
                                i: f'{i: .2f}'
                                for i in np.arange(min_val, max_val +
                                                   0.1, 0.25)
                                # for i in np.arange(min_val, max_val +
                                #                    0.001, 0.1)
                            },
                            tooltip={
                                "placement": "bottom",
                                "always_visible": True
                            },
                            className="slider-input"),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center"
                    },
                )
                for col, (min_val,
                          max_val) in zip(decision_variables.keys(), [(0, 1)] *
                                          len(decision_variables))
            ]

            return fig, df.to_dict('records'), sliders

    return dash.no_update, [], []

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

@app.callback(Output('graph1', "figure"),
              [Input({
                  "type": "ds-sliders",
                  "index": ALL
              }, "value")], [
                  State('graph1', "figure"),
                  State('stored-df', 'data'),
                  State('slider-values-store', 'data')
              ],
              prevent_initial_call=True)
def pareto_front(slider_values, fig, data, stored_slider_values):
    print("Slider values: ", slider_values)
    
    if slider_values != stored_slider_values:
        stored_slider_values = slider_values
        if not slider_values or slider_values == [0] * len(slider_values):
            return fig
        if data is None:
            return fig

    # if stored_slider_values is None or slider_values != stored_slider_values:
        n_var = len(slider_values)
        n_obj = len(data[0]) - n_var
        DTLZ2 = get_problem("dtlz2", n_var=n_var, n_obj=n_obj)
        dff = DTLZ2.evaluate(np.array(slider_values))
        print(dff)

        fig = gen_graph(pd.DataFrame.from_dict(data))
        fig.update_layout(showlegend=False)
        # fig.update_traces(hovertemplate='<b>f1</b>: %{x}' +
        #                   '<br><b>f2</b>: %{y}<extra></extra>',
        #                   hoverlabel=dict(font_size=22))

        fig.add_scatter(x=[dff[0]],
                            y=[dff[1]],
                            marker=dict(color='blue', size=30, symbol='star'),
                            hoverinfo='text',
                            text=f'f1: {dff[0]: .2f}<br>f2: {dff[1]: .2f}',
                            hoverlabel=dict(font_size=22)
                            )
    else:
        return fig

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
