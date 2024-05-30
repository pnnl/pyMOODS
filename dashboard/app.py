import base64, io
import json
import pandas as pd
import numpy as np
import dash
from dash import dcc, html, Dash, ctx
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
from pymoo.problems import get_problem
import plotly.graph_objs as go
from dashlib.layout import interface_layout
from dashlib.components import gen_graph, blank_figure
from data.parser import parse_data
from logger.custom import NumpyEncoder
from dash.exceptions import PreventUpdate
from pymoo.optimize import minimize
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
)

new_markers = {}

for i in np.arange(0, 1.01, 0.25):
    if isinstance(i, float) and i == int(i):
        new_markers[int(i)] = f'{int(i)}'
    else:
        new_markers[i] = f'{i:.2f}'

labelFlex = {
    'flexShrink': 0,
    'fontFamily': "Helvetica",
}
event = {"event": "click", "props": ['shiftKey']}


def generate_data_dtlz4(n_var, n_obj):
    problem = get_problem('dtlz1', n_var=n_var, n_obj=n_obj)
    algorithm = NSGA2(pop_size=300)
    res = minimize(problem, algorithm, ('n_gen', 300), seed=1, verbose=False)

    X = res.X
    F = res.F
    n_var = problem.n_var
    n_obj = problem.n_obj
    var_cols = [f'x{i}' for i in range(1, n_var + 1)]
    obj_cols = [f'f{i}' for i in range(1, n_obj + 1)]
    df = pd.DataFrame(X, columns=var_cols)
    for i in range(n_obj):
        df[obj_cols[i]] = F[:, i]

    # front = res.F
    # print("Generated Data: ")
    # print(df.head())
    return df


app.layout = html.Div([
    dcc.Store(id="slider-values-store", data={}),
    dcc.Store(id="slider-change-status", data=False),
    dcc.Store(id="df-dimensions", data={}),
    dcc.Store(id='decision-variables-store', data={}),
    dcc.Store(id="decision-values-store", data=[]),
    dcc.Store(id='temp-decision-values-store', data=[]),
    dcc.Store(id='selected-radar-pts-store', data=[]),
    dcc.Store(id='selected-obj-pts-store', data=[]),
    dcc.Store(id='temp-summary-min-max', data=[]),
    interface_layout,
    html.Div(id="radar-sliders", style={'display': 'none'}),
    dcc.Store(id='shift-is-clicked', data=False),
    # dcc.Graph(id="radar-chart"),
])


@app.callback(Output("shift-is-clicked", "data"),
              Input("el", "n_events"),
              State("el", "event"),
              State('graph1', 'clickData'),
              State('shift-is-clicked', 'data'),
              State('selected-obj-pts-store', 'data'),
              prevent_initial_call=True)
def click_event(n_events, e, click_data, curr_shift, obj_pts_store):
    if click_data is None:
        raise PreventUpdate
    else:
        if 'points' in obj_pts_store:
            if click_data['points'][0] in obj_pts_store['points']:
                raise PreventUpdate
            return e['shiftKey']
        return e['shiftKey']


@app.callback(Output("data-generated", "data"),
              [Input("generated-dtlz4-button", "n_clicks")], [
                  State("num-decision-vars", "value"),
                  State("num-objective-vars", "value"),
              ])
def generate_data_dtlz4_callback(n_clicks, n_var, n_obj):
    if n_var is None or n_obj is None:
        raise dash.exceptions.PreventUpdate("Please enter")
    if n_clicks is None:
        raise PreventUpdate

    df_generated = generate_data_dtlz4(n_var=n_var, n_obj=n_obj)
    # filename = "data_generated.json"
    # print("Generated JSON: ",df_generated.to_json(orient='records'))
    return df_generated.to_json(orient='records')


@app.callback(Output("summary-table", 'style'),
              Output("summary-table", 'children'),
              Output('df-dimensions', 'data'),
              Output('decision-variables-store', 'data'),
              Output('decision-values-store', 'data'),
              Output('selected-obj-pts-store', 'data'),
              Output('selected-radar-pts-store', 'data'), [
                  Input('upload-data', 'contents'),
                  Input('upload-data', 'filename'),
                  Input("data-generated", "data")
              ],
              prevent_initial_call=True)
def update_summary(contents, filename, generated_data):
    if generated_data:
        generated_data_io = io.StringIO(generated_data)
        df = pd.read_json(generated_data_io, orient='records')
        # print(df.shape)
    elif contents is None:
        return {'display': 'none'}, [], {}, [], dash.no_update, [], []
    else:
        #parse the uploaded file
        content_type, content_string = contents[0].split(',')
        decoded = base64.b64decode(content_string)
        file = json.loads(decoded)

        df = pd.DataFrame(file)

    decision_variables = [col for col in df.columns if col.startswith('x')]
    objective_functions = [col for col in df.columns if col.startswith('f')]

    size = len(df)

    summary_table = html.Table([
        html.Tr([
            html.Td(html.H3("SUMMARY"),
                    style={
                        'textAlign': 'center',
                        'paddingLeft': '3.5rem'
                    }),
            html.Td(),
            html.Td(),
        ]),
        html.Tr([
            html.Td(html.H4("#Decision Variables:"),
                    style={'padding': '0.2rem'}),
            html.Td(html.H4(len(decision_variables)),
                    style={
                        'color': 'blue',
                        'padding': '0.5rem'
                    })
        ]),
        html.Tr([
            html.Td(html.H4("#Objective Variables:"),
                    style={'padding': '0.2rem'}),
            html.Td(html.H4(len(objective_functions)),
                    style={
                        'color': 'blue',
                        'padding': '0.5rem'
                    })
        ]),
        html.Tr([
            html.Td(html.H4("Size of Pareto Front:  "),
                    style={'padding': '0.2rem'}),
            html.Td(html.H4(size),
                    style={
                        'color': 'blue',
                        'padding': '0.5rem'
                    })
        ]),
    ])

    return {
        'margin': '10rem auto auto auto',
        'fontWeight': '500',
        'borderRadius': '10px',
        'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.8)',
        'padding': '1.7rem',
        'fontFamily': 'Arial, Helvetica, sans-serif',
        'textAlign': 'center',
        'width': '82%',
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
    }, summary_table, {
        'obj': len(objective_functions),
        'dec': len(decision_variables)
    }, decision_variables, [[0]] * len(decision_variables), [], []


@app.callback(Output("graph1", "figure", allow_duplicate=True),
              Output("stored-df", "data"),
              Output("sliders", "children"),
              Output("slider-change-status", "data"),
              Output('temp-summary-min-max', 'data'),
              Input("upload-data", "contents"),
              Input("upload-data", "filename"),
              Input('tabs-example-graph', 'value'),
              Input({
                  "type": "ds-sliders",
                  "index": ALL
              }, "value"),
              Input("graph1", "clickData"),
              Input('graph1', 'selectedData'),
              Input('df-dimensions', 'data'),
              Input('decision-variables-store', 'data'),
              Input('decision-values-store', 'data'),
              Input("data-generated", "data"),
              State('selected-radar-pts-store', 'data'),
              prevent_initial_call=True)
def update_output(contents, filename, tab, slider_values, click_data,
                  selected_data, dimensions, decision_vars, decision_values,
                  generated_data, selection_store):
    if len(dimensions) == 0:
        raise PreventUpdate

    if generated_data:
        df, decision_variables, objective_functions = parse_data(
            generated_data)

    elif contents is not None:
        contents = contents[0]
        filename = filename[0]
        df, decision_variables, objective_functions = parse_data(
            contents, filename)
    else:
        df = pd.DataFrame()

    changed_id = [p['prop_id'] for p in dash.callback_context.triggered]

    # print('update output callback', changed_id)

    if df is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


#     if len(changed_id) == len(decision_variables) + 1:
#         return dash.no_update, dash.no_update, dash.no_update, False
    if 'slider' in changed_id[0]:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True
    elif ('upload-data' in changed_id[0]) | ('data-generated.data'
                                             in changed_id):
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
            json.dump(categorized_data, outfile, cls=NumpyEncoder, indent=4)

        fig = gen_graph(df)
        sliders = []
        if dimensions['dec'] < 5:

            # for var in decision_variables:
            for var, (min_val,
                      max_val) in zip(decision_variables.keys(),
                                      [(0, 1)] * len(decision_variables)):
                sliders.append(
                    html.Div(
                        [
                            html.Label(f'{var}',
                                       style=labelFlex,
                                       className="slider-label"),
                            dcc.RangeSlider(
                                id={
                                    'type': 'ds-sliders',
                                    'index': f'slider-{var}'
                                },
                                min=min_val,
                                max=max_val,
                                step=0.01,
                                marks={
                                    i: f'{i: .2f}'
                                    for i in np.arange(min_val, max_val +
                                                       0.1, 0.25)
                                },
                                tooltip={
                                    "placement": "bottom",
                                    "always_visible": True
                                },
                                className="slider-input",
                            )
                        ],
                        style={
                            'display': 'flex',
                            'alignItems': 'center',
                            # 'flexDirection': 'column',
                            'padding': '10px',
                            'width': '100%',
                        },
                        # className='slider-5'
                    ))

            if selected_data:
                selected_points = selected_data.get('points', [])
                if selected_points:
                    selected_indices = [
                        point['pointIndex'] for point in selected_points
                    ]
                    selected_df = df.iloc[selected_indices]
                    for slider in sliders:
                        var = slider['props']['children'][1]['props']['id'][
                            'index']
                        # var = slider['index'].split('-')[-1]
                        print("Varrr", var)
                        if var in selected_df:
                            min_val = selected_df[var].min()
                            max_val = selected_df[var].max()
                            slider['props']['children'][1]['props'][
                                'value'] = [min_val, max_val]

            return fig, df.to_dict('records'), html.Div(
                sliders,
                style={
                    'display': 'flex',
                    'flexDirection': 'column',
                    'alignItems': 'center',
                    'width': '100%',
                    'padding': '2%'
                    # 'justifyContent':
                    # 'center'
                }), False, {}

        if dimensions['dec'] >= 5:

            rad_sliders = []
            default_r = [0] * len(decision_variables.keys())
            default_th = list(decision_variables.keys())

            for x in range(len(default_r)):
                rad_sliders.append(
                    html.Div(
                        [
                            html.P(f"x{x+1}", style={'fontSize': '18px'}),
                            dcc.Slider(id={
                                'type': 'dec-sliders',
                                'index': f'rad-slider-{x+1}'
                            },
                                       min=0,
                                       max=1,
                                       step=0.01,
                                       marks=new_markers,
                                       tooltip={
                                           "placement": "bottom",
                                           "always_visible": True
                                       },
                                       value=default_r[x],
                                       className='slider-5')
                        ],
                        style={
                            'display': 'flex',
                            'alignItems': 'center',
                            'width': '100%',
                        }))

            rad_fig = go.Figure(data=go.Scatterpolar(
                r=default_r, theta=default_th, line_color='red'))
            rad_fig.update_layout(dragmode='select',
                                  margin=dict(l=20, r=20, t=20, b=20))

            return fig, df.to_dict('records'), html.Div(
                [
                    html.H6(id='help'),
                    dcc.Graph(id='radar-chart',
                              figure=rad_fig,
                              style={
                                  'width': '95%',
                                  'height': '100%'
                              }),
                    html.Div(id='radar-sliders', style={'display': 'none'}),
                ],
                style={
                    'display': 'flex',
                    'flexDirection': 'column',
                    'alignItems': 'center',
                    'justifyContent': 'space-between'
                }), False, []

        sliders = [
            html.Div(
                [
                    html.H6(id='help'),
                    html.Div(col, style=labelFlex, className="slider-label"),
                    dcc.Graph(id='radar-chart', style={'display': 'none'}),
                    html.Div(id='radar-sliders', style={'display': 'none'}),
                    dcc.Slider(
                        id={
                            'type': 'ds-sliders',
                            'index': f'slider-{col}'
                        },
                        min=min_val,
                        max=max_val,
                        # step=round((max_val - min_val) / 4, 2),
                        step=0.01,
                        marks={
                            i: f'{i: .2f}'
                            for i in np.arange(min_val, max_val + 0.1, 0.25)
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
            ) for col, (min_val,
                        max_val) in zip(decision_variables.keys(), [(0, 1)] *
                                        len(decision_variables))
        ]

        return fig, df.to_dict('records'), sliders, False, dash.no_update
    elif selected_data:
        if selection_store is None:
            if dimensions['dec'] >= 5:
                rad_fig = go.Figure()

                if len(decision_values) > 0:
                    print('decision_values', len(decision_values))
                    merged = {}
                    new_th = decision_vars.copy()
                    new_th.append(decision_vars[0])

                    for i, var in enumerate(decision_vars):
                        values = [
                            solution[i] for solution in decision_values
                            if len(solution) == len(decision_vars)
                        ]

                        if len(values) > 0:
                            merged[var] = {
                                'min': min(values),
                                'max': max(values)
                            }

                    if len(merged) > 0:
                        rad_fig.add_trace(
                            go.Scatterpolar(
                                r=[merged[x]['min'] for x in new_th],
                                theta=new_th,
                                fill='toself',
                                mode='lines',
                                name='Min solutions'))
                        rad_fig.add_trace(
                            go.Scatterpolar(
                                r=[merged[x]['max'] for x in new_th],
                                theta=new_th,
                                fill='toself',
                                mode='lines',
                                name='Max solutions'))

                    for solution in decision_values:
                        new_r = solution
                        new_r.append(solution[0])
                        rad_fig.add_trace(
                            go.Scatterpolar(r=new_r, theta=new_th))

                rad_fig.update_layout(
                    showlegend=False,
                    dragmode='select',
                    margin=dict(l=20, r=20, t=20, b=20),
                    polar=dict(radialaxis=dict(range=[
                        0, max(list(map(max, decision_values))) + 0.1
                    ],
                                               showticklabels=True)))

                return dash.no_update, dash.no_update, html.Div(
                    [
                        html.
                        H6(id='help',
                           children=
                           'Click and drag to draw a box around the area containing the points to filter. (The box should contain points, not just lines.)'
                           ),
                        html.Div(
                            [
                                dcc.Graph(id='radar-chart',
                                          figure=rad_fig,
                                          style={
                                              'width': '95%',
                                              'height': '95%'
                                          }),
                                html.Div(id='radar-sliders',
                                         style={'display': 'none'})
                            ],
                            style={
                                'display': 'flex',
                                'alignItems': 'center',
                                'justifyContent': 'space-between',
                                'width': '100%',
                                'height': '100%'
                            })
                    ],
                    style={
                        'display': 'flex',
                        'flexDirection': 'column',
                        'alignItems': 'center',
                        'justifyContent': 'space-between'
                    }), False, merged
        raise PreventUpdate

    # TO REMOVE CLICK
    elif click_data:
        if selection_store is None:
            if dimensions['dec'] >= 5:
                rad_fig = go.Figure()

                if len(decision_values) > 0:
                    print('decision_values', len(decision_values))
                    merged = {}
                    new_th = decision_vars.copy()
                    new_th.append(decision_vars[0])
                    for i, var in enumerate(decision_vars):
                        values = [
                            solution[i] for solution in decision_values
                            if len(solution) == len(decision_vars)
                        ]

                        if len(values) > 0:
                            merged[var] = {
                                'min': min(values),
                                'max': max(values)
                            }

                    if len(merged) > 0:
                        rad_fig.add_trace(
                            go.Scatterpolar(
                                r=[merged[x]['min'] for x in new_th],
                                theta=new_th,
                                fill='toself',
                                mode='lines',
                                name='Min solutions'))
                        rad_fig.add_trace(
                            go.Scatterpolar(
                                r=[merged[x]['max'] for x in new_th],
                                theta=new_th,
                                fill='toself',
                                mode='lines',
                                name='Max solutions'))

                    for solution in decision_values:
                        new_r = solution
                        new_r.append(solution[0])
                        # print(new_r, new_th)
                        rad_fig.add_trace(
                            go.Scatterpolar(r=new_r, theta=new_th))

                    rad_fig.update_layout(
                        showlegend=False,
                        dragmode='select',
                        margin=dict(l=20, r=20, t=20, b=20),
                        polar=dict(radialaxis=dict(range=[
                            0, max(list(map(max, decision_values))) + 0.1
                        ],
                                                   showticklabels=True)))
                    return dash.no_update, dash.no_update, html.Div(
                        [
                            html.
                            H6(id='help',
                               children=
                               'Click and drag to draw a box around the area containing the points to filter. (The box should contain points, not just lines.)'
                               ),
                            html.Div(
                                [
                                    dcc.Graph(id='radar-chart',
                                              figure=rad_fig,
                                              style={
                                                  'width': '95%',
                                                  'height': '95%'
                                              }),
                                    html.Div(id='radar-sliders',
                                             style={'display': 'none'})
                                ],
                                style={
                                    'display': 'flex',
                                    'alignItems': 'center',
                                    'justifyContent': 'space-between',
                                    'width': '100%',
                                    'height': '100%'
                                })
                        ],
                        style={
                            'display': 'flex',
                            'flexDirection': 'column',
                            'alignItems': 'center',
                            'justifyContent': 'space-between'
                        }), False, merged
        raise PreventUpdate

    return dash.no_update, dash.no_update, dash.no_update, False, dash.no_update


@app.callback(Output('radar-chart', 'figure', allow_duplicate=True),
              Output('slider-change-status', 'data', allow_duplicate=True),
              Output('decision-values-store', 'data', allow_duplicate=True),
              Output('no-data-alert', 'is_open'),
              Input({
                  'type': 'dec-sliders',
                  'index': ALL,
              }, 'value'),
              Input('radar-chart', 'figure'),
              State('decision-values-store', 'data'),
              State('decision-variables-store', 'data'),
              State('selected-radar-pts-store', 'data'),
              State('selected-obj-pts-store', 'data'),
              State('stored-df', 'data'),
              State('df-dimensions', 'data'),
              prevent_initial_call=True)
def update_radar_from_slider(slider_values, fig, dec_values, dec_vars,
                             radar_pts, obj_pts, data, dims):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered]

    if radar_pts is None:
        return dash.no_update, False, dash.no_update, False
    if 'radar-chart.figure' in changed_id:
        return dash.no_update, False, dash.no_update, dash.no_update
    if 'shapes' in fig['layout']:
        # slider value changed
        if len(changed_id) == 1:
            filtered_th = sorted(
                list(set([obj['theta'] for obj in radar_pts['points']])))
            #             print('filtered_th', filtered_th)
            if obj_pts['points']:
                df = pd.DataFrame(data)
                if dims['obj'] < 4:
                    trace_indices = [
                        obj['pointNumber'] for obj in obj_pts["points"]
                    ]
#                     [obj['pointNumber'] for obj in obj_pts_store["points"]]
                else:
                    trace_indices = [
                        obj['curveNumber'] for obj in obj_pts["points"]
                    ]
                subset = df.iloc[trace_indices, :len(dec_vars)].astype(float)


#             print('checking', trace_indices, subset)

            curr_data = fig['data'].copy()
            updated_slider = {}
            for i, th in enumerate(filtered_th):
                updated_slider[th] = slider_values[i]

            area_obj = [d for d in curr_data if 'name' in d]
            curr_solutions = [{
                'r': el,
                'theta': dec_vars,
                'type': 'scatterpolar'
            } for el in subset.values.tolist()]

            for obj in area_obj:
                for k, v in updated_slider.items():
                    i = dec_vars.index(k)
                    if obj['name'] == 'Min solutions':
                        obj['r'][i] = v[0]
                        if i == 0:
                            obj['r'][-1] = v[0]
                    if obj['name'] == 'Max solutions':
                        obj['r'][i] = v[1]
                        if i == 0:
                            obj['r'][-1] = v[1]

            filtered_data = area_obj

            for d in curr_solutions:
                statuses = []
                for k, v in updated_slider.items():
                    i = dec_vars.index(k)
                    statuses.append((d['r'][i] >= v[0]) & (d['r'][i] <= v[1]))

                if sum(statuses) == len(filtered_th):
                    filtered_data.append(d)
            solutions = [d for d in filtered_data if 'name' not in d.keys()]

            fig['data'] = filtered_data
            if len(solutions) > 0:
                return fig, True, [sol['r'] for sol in solutions], False
            else:
                print('here, set is_open to True')
                return dash.no_update, dash.no_update, dash.no_update, True

        raise PreventUpdate
    raise PreventUpdate


@app.callback(Output('selected-radar-pts-store', 'data', allow_duplicate=True),
              Output('selected-obj-pts-store', 'data', allow_duplicate=True),
              Input('radar-chart', 'selectedData'),
              Input({
                  "type": "dec-sliders",
                  "index": ALL
              }, "value"),
              Input('graph1', 'clickData'),
              Input('graph1', 'selectedData'),
              Input('shift-is-clicked', 'data'),
              State('decision-variables-store', 'data'),
              State('selected-obj-pts-store', 'data'),
              prevent_initial_call=True)
def save_selection(radar_selected, dec_sliders, click_data, selected_data,
                   shift, dec_vars, curr_obj_pts):
    if len(dec_vars) >= 5:
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
        if 'rad-slider-' in changed_id[0]:
            raise PreventUpdate
        if ('shift-is-clicked.data' in changed_id):
            if click_data:
                if shift:
                    tmp = curr_obj_pts
                    tmp['points'].append(click_data['points'][0])
                    return None, tmp
                return None, click_data
            raise PreventUpdate
        if changed_id[0] == 'graph1.selectedData':
            if len(selected_data['points']) == 0:
                raise PreventUpdate
            return None, selected_data
        return radar_selected, dash.no_update
    raise PreventUpdate


@app.callback(Output('radar-sliders', 'children'),
              Output('radar-sliders', 'style'),
              Output('radar-chart', 'style'),
              Output('radar-chart', 'figure', allow_duplicate=True),
              Output('help', 'children'),
              Output('slider-change-status', 'data', allow_duplicate=True),
              Input('radar-chart', 'selectedData'),
              Input('radar-chart', 'figure'),
              Input({
                  "type": "dec-sliders",
                  "index": ALL
              }, "value"),
              State('temp-summary-min-max', 'data'),
              State('decision-values-store', 'data'),
              State('decision-variables-store', 'data'),
              State('graph1', 'figure'),
              prevent_initial_call=True)
def filter_sliders(selected_radar_values, fig, dec_slider_values, summary,
                   stored_sliders, decision_vars, pc_fig):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
    # print('filter sliders callback', changed_id)
    if selected_radar_values:
        filtered_vars = sorted(list(
            set([obj['theta'] for obj in selected_radar_values['points']])),
                               key=lambda x: int(x.split('x')[1]))
        filtered_indices = [decision_vars.index(x) for x in filtered_vars]

        new_sliders = []
        for v in filtered_vars:
            idx = decision_vars.index(v)
            val = [
                min([values[idx] for values in stored_sliders]),
                max([values[idx] for values in stored_sliders])
            ]
            if ('rad-slider' in changed_id[0]) | (changed_id[0]
                                                  == 'radar-chart.figure'):

                i = filtered_vars.index(v)
                val = [dec_slider_values[i][0], dec_slider_values[i][1]]

            new_sliders.append(
                html.Div(
                    [
                        html.P(f"{v}", style={'fontSize': '18px'}),
                        dcc.RangeSlider(
                            id={
                                'type': 'dec-sliders',
                                'index': f'rad-slider-{decision_vars.index(v)}'
                            },
                            min=0,
                            max=1,
                            step=0.01,
                            marks=new_markers,
                            tooltip={
                                "placement": "bottom",
                                "always_visible": True
                            },
                            value=val,
                            className='slider-5')
                    ],
                    style={
                        'display': 'flex',
                        'alignItems': 'center',
                        'width': '100%',
                        'padding': '2%'
                    }))

        new_th = decision_vars
        new_th.append(decision_vars[0])

        chartAxisRange = fig['layout']['polar']['radialaxis']['range']
        boundingBox = selected_radar_values['range']

        converted_x = []
        converted_y = []
        for x in boundingBox['x']:
            # convert scale to use chart axis range
            tmp_x = x + chartAxisRange[1]
            # calculate percentage on scale
            perc_x = tmp_x / (chartAxisRange[1] * 2)
            # re-calculate on a different scale
            converted_x.append(perc_x)

        for y in boundingBox['y']:
            # convert scale to use chart axis range
            tmp_y = y + chartAxisRange[1]
            # calculate percentage on scale
            perc_y = tmp_y / (chartAxisRange[1] * 2)
            # re-calculate on a different scale
            converted_y.append(perc_y * (0.85 - 0.15) + 0.15)

        rad_fig = go.Figure(fig)

        if changed_id[0] == 'radar-chart.selectedData':
            rad_fig['layout'].update(shapes=[
                dict(type="rect",
                     x0=converted_x[0],
                     x1=converted_x[1],
                     y0=converted_y[0],
                     y1=converted_y[1],
                     xref='x domain',
                     yref='y domain',
                     xsizemode='scaled',
                     ysizemode='scaled',
                     line=dict(color="black", dash='dot', width=1))
            ])

        rad_fig.update_layout(showlegend=False,
                              dragmode='select',
                              margin=dict(l=20, r=20, t=20, b=20))
        return new_sliders, {
            'display': 'block',
            'width': '45%'
        }, {
            'width': '50%',
            'height': '100%'
        }, rad_fig, 'Move the sliders to modify the values of filtered variables and double-click on an empty area in the chart to deselect.', dash.no_update
    else:
        if len(decision_vars) >= 5:
            th = decision_vars
            th.append(decision_vars[0])

            rad_fig = go.Figure()
            if len(summary) > 0:
                rad_fig.add_trace(
                    go.Scatterpolar(r=[summary[x]['min'] for x in th],
                                    theta=th,
                                    fill='toself',
                                    mode='lines',
                                    name='Minimum'))
                rad_fig.add_trace(
                    go.Scatterpolar(r=[summary[x]['max'] for x in th],
                                    theta=th,
                                    fill='toself',
                                    mode='lines',
                                    name='Maximum'))
            for solution in stored_sliders:
                r = solution
                r.append(solution[0])
                rad_fig.add_trace(go.Scatterpolar(r=r, theta=th))

            rad_fig.update_layout(showlegend=False,
                                  dragmode='select',
                                  margin=dict(l=20, r=20, t=20, b=20))

            if (len(changed_id) == 1) & (changed_id[0]
                                         == 'radar-chart.selectedData'):
                fig['layout'].update(shapes=[])

                return dash.no_update, {
                    'display': 'none'
                }, {
                    'width': '95%',
                    'height': '100%'
                }, fig, 'Click and drag to draw a box around the area containing the points to filter. (The box should contain points, not just lines.)', False
            return dash.no_update, {
                'display': 'none'
            }, {
                'width': '95%',
                'height': '100%'
            }, dash.no_update, 'Click and drag to draw a box around the area containing the points to filter. (The box should contain points, not just lines.)', dash.no_update
        raise PreventUpdate


@app.callback(Output({
    "type": "ds-sliders",
    "index": ALL
}, "value"),
              Output('decision-values-store', 'data', allow_duplicate=True),
              Input('graph1', 'clickData'),
              Input('selected-obj-pts-store', 'data'),
              Input('graph1', 'selectedData'), [
                  State('stored-df', 'data'),
                  State({
                      "type": "ds-sliders",
                      "index": ALL
                  }, "id"),
                  State('decision-variables-store', 'data')
              ],
              prevent_initial_call=True)
def slider_output(click_data, obj_pts_store, selected_data, my_data,
                  slider_ids, dec_vars):
    if selected_data and my_data:
        df = pd.DataFrame(my_data)
        # if 'points' in selected_data and len(selected_data['points']) > 0:
        num_objectives = len(
            [col for col in df.columns if col.startswith('f')])
        num_decision_vars = len(df.columns) - num_objectives
        if click_data:
            if num_objectives == 3:
                x_key = 'x'
                y_key = 'y'
                z_key = 'z'

                if 'points' in obj_pts_store and len(
                        obj_pts_store['points']) > 0:
                    trace_indices = [
                        obj['pointNumber'] for obj in obj_pts_store["points"]
                    ]
                    print('trace_indices checking', trace_indices)
                    subset = df.iloc[trace_indices, :num_decision_vars].astype(
                        float)
                    return [], subset.values.tolist()

            # print('selected_data[points]', selected_data['points'])
        if selected_data:

            if 'points' in selected_data and len(selected_data['points']) > 0:
                x_key = 'x'
                y_key = 'y'
                z_key = 'z' if num_objectives >= 3 else None

                if num_decision_vars >= 5:
                    if num_objectives < 4:
                        trace_indices = [
                            obj['pointNumber']
                            for obj in selected_data["points"]
                        ]
                        subset = df.iloc[
                            trace_indices, :num_decision_vars].astype(float)
                        # print('trace indices >=5 < 4', trace_indices)
                        # print('print values', subset.values.tolist())
                    else:
                        trace_indices = [
                            obj['curveNumber']
                            for obj in selected_data["points"]
                        ]
                        subset = df.iloc[
                            trace_indices, :num_decision_vars].astype(float)
                        # print('trace indices  >=5 > 4', trace_indices)
                        # print('print values', subset.values.tolist())
                    return [], subset.values.tolist()
                elif num_decision_vars < 5:
                    if num_objectives < 4:
                        trace_indices = [
                            obj['pointIndex']
                            for obj in selected_data['points']
                        ]
                        subset = df.iloc[
                            trace_indices, :num_decision_vars].astype(float)
                        # print('rows', df.iloc[trace_indices, ].astype(float))
                        # print('trace indices <5 < 4', trace_indices)
                        # print('print values', subset.values.tolist())
                    else:
                        trace_indices = [
                            obj['curveNumber']
                            for obj in selected_data['points']
                        ]
                        subset = df.iloc[
                            trace_indices, :num_decision_vars].astype(float)
                        # print('trace indices <5 > 4', trace_indices)
                        # print('print values', subset.values.tolist())
                        print('rows', df.iloc[
                            trace_indices,
                        ].astype(float))
                    slider_values = []
                    for slider_id in slider_ids:
                        var = slider_id['index'].split('-')[-1]
                        print("V", var)
                        if var in subset:
                            min_val = subset[var].min()
                            print("Min", min_val)
                            max_val = subset[var].max()
                            print("Max", max_val)
                            slider_values.append([min_val, max_val])

                            print("Slmmm: ", slider_values)
                        # else:
                        #     slider_values.append([0, 1])
                        #     print("Sl2: ",slider_values)

                print("SLider", slider_values)
                return slider_values, subset.values.tolist()

            # return subset.values.tolist(), []
            return [], []
    raise PreventUpdate


# @app.callback(
#     Output('graph1', "figure"),
#     [
#         Input({
#             "type": "ds-sliders",
#             "index": ALL
#         }, "value"),
#         Input({
#             "type": "dec-sliders",
#             "index": ALL
#         }, "value"),
#         Input('decision-values-store', 'data'),
#         Input('graph1', 'clickData'),
#         Input('graph1', 'selectedData'),
#         Input('slider-change-status', 'data'),
#         Input('graph1', "figure"),
#         Input('radar-sliders', 'style'),
#         Input('selected-obj-pts-store', 'data'),
#         Input('generated-dtlz4-button', 'n_clicks'),
#     ],
#     [
#         State('stored-df', 'data'),
#         State('slider-values-store', 'data'),
#         State('df-dimensions', 'data'),
#         State('selected-radar-pts-store', 'data'),
#         State('decision-variables-store', 'data'),
#     ],
#     prevent_initial_call=True)

# def pareto_front(ds_slider_values, dec_slider_values, dec_values_store, click_data, selected_data, change_status, curr_fig, rad_sliders_style, obj_pts_store, generated_data,
#                  data, stored_slider_values, dims, selection_store, dec_vars_store):

#     changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
# #     print('pareto', changed_id, change_status)

#     slider_values = ds_slider_values
#     if dims['dec'] >= 5:
#         slider_values = dec_values_store

#     if slider_values != stored_slider_values:
#         stored_slider_values = slider_values
# #         if not slider_values or all(slider == 0 for slider in slider_values):
# #             return fig
#         if data is None:
#             return curr_fig
#     df = pd.DataFrame.from_dict(data)
#     fig = gen_graph(pd.DataFrame.from_dict(data))
#     if 'points' in obj_pts_store:
#         print('obj_pts_store', len(obj_pts_store['points']))
#     # if len(fig.data) > 1:
#     #     fig.data = [fig.data[0]]
#     # Adding new scatter trace for the newly selected point:
#     if change_status is True:
#         if not slider_values or all(slider == 0 for slider in slider_values):
#             return fig
#         if changed_id[0] == 'graph1.selectedData':
#             raise PreventUpdate
#         # click_data = None
#         n_var = dims['dec']
#         n_obj = dims['obj']

#         DTLZ2 = get_problem("dtlz2", n_var=n_var, n_obj=n_obj)
#         dff = DTLZ2.evaluate(np.array([0 if x is None else x for x in slider_values]))
#         df = pd.DataFrame(data)
#         num_objectives = len([col for col in df.columns if col.startswith('f')])

#         if num_objectives == 2:
#             if isinstance(fig.data[0], go.Scatter):
#                 for el in dff:
#                     fig.add_scatter(x=[el[0]],
#                                     y=[el[1]],
#                                     mode='markers',
#                                     marker=dict(color='red',
#                                                 size=30,
#                                                 symbol='star'),
#                                     hoverinfo='text',
#                                     text=f'f1: {el[0]: .2f}<br>f2: {el[1]: .2f}',
#                                     hoverlabel=dict(font_size=22))
#         elif num_objectives == 3:
#             if isinstance(fig.data[0], go.Scatter3d):
#                 for el in dff:
#                     fig.add_scatter3d(
#                         x=[el[0]],
#                         y=[el[1]],
#                         z=[el[2]],
#                         mode='markers',
#                         marker=dict(color='red', size=30),
#                         hoverinfo='text',
#                         text=
#                         f'f1: {el[0]: .2f}<br>f2: {el[1]: .2f}<br>f3: {el[2]: .2f}',
#                         hoverlabel=dict(font_size=22))
#         elif num_objectives > 3:
#             if isinstance(fig.data[0], go.Scatter):
#                 x_labels = [f'f{i+1}' for i in range(len(dff))]

#                 for el in dff:
#                     fig.add_scatter(
#                         x=x_labels,
#                         y=el,
#                         mode='lines+markers',
#                         line=dict(color='red', width=5),
#                         marker=dict(color='red', size=30, symbol='star'),
#                         hoverinfo='text',
#                         text='<br>'.join([
#                             f'{label}: {value: .2f}'
#                             for label, value in zip(x_labels, el)
#                         ]),
#                         # text=f'f1: {dff[0]: .2f}<br>f2: {dff[1]: .2f}<br>f3: {dff[2]: .2f}<br>f4: {dff[3]: .2f}',
#                         hoverlabel=dict(font_size=22))
#     else:
#         test = curr_fig['data']
#         num_symbols = len([d for d in test if ('marker' in d.keys())])
#         if dims['obj'] != 3:
# #         if selected_data:
#             if selected_data:
#                 # print('if selected_data points')
#                 if len(changed_id) == 5:
#                     ranges = obj_pts_store['range']
#                     selection_bounds = {
#                         "x0": ranges["x"][0],
#                         "x1": ranges["x"][1],
#                         "y0": ranges["y"][0],
#                         "y1": ranges["y"][1],
#                     }

#                     fig.add_shape(
#                         dict(
#                             {"type": "rect", "line": {"width": 1.5, "dash": "dot", "color": "black"}},
#                             **selection_bounds
#                         )
#                     )
#                     fig.update_layout(showlegend=False)
#                     return fig
#                 else:
#                     raise PreventUpdate
#             else:
#                 if num_symbols > 0:
#                     fig.update(data=[d for d in test if ('marker' not in d.keys())])
#                     if 'generated-dtlz4-button.n_clicks' in changed_id:
#                         fig['layout'].update(shapes=[])
#                     else:
#                         ranges = obj_pts_store['range']
#                         selection_bounds = {
#                             "x0": ranges["x"][0],
#                             "x1": ranges["x"][1],
#                             "y0": ranges["y"][0],
#                             "y1": ranges["y"][1],
#                         }
#                         fig.add_shape(
#                             dict(
#                                 {"type": "rect", "line": {"width": 1.5, "dash": "dot", "color": "black"}},
#                                 **selection_bounds
#                             )
#                         )
#                 else:
#                     raise PreventUpdate

#         # raise PreventUpdate

#         # fig = gen_graph(pd.DataFrame.from_dict(data))

#         # REMOVE CLICK
#         if dims['obj'] == 3:
# #         if click_data:
#             if isinstance(fig.data[0], go.Scatter3d):
#                 if 'points' in obj_pts_store:
#                     for pt in obj_pts_store['points']:
#                         f1_point = pt['x']
#                         f2_point = pt['y']
#                         f3_point = pt['z']

#                         fig.add_scatter3d(
#                             x=[f1_point],
#                             y=[f2_point],
#                             z=[f3_point],
#                             mode='markers',
#                             marker=dict(color=f"rgb(32,178,170)", size=16),
#                             text=f'f1: {f1_point: .2f}<br>f2: {f2_point: .2f}<br>f3: {f3_point: .2f}',
#                             hoverlabel=dict(font_size=28)
#                         )
#                         fig.update_traces(hovertemplate='f1: %{x}<br>f2: %{y}<br>f3: %{z}<extra></extra>')
# #             if isinstance(fig.data[0], go.Scatter):
# #                 f1_point = click_data['points'][0]['x']
# #                 f2_point = click_data['points'][0]['y']
# #                 selected_trace_index = click_data['points'][0]['curveNumber']
# #                 selected_trace = fig.data[selected_trace_index]

# #                 # if selected_trace:
# #                 if isinstance(selected_trace,
# #                               go.Scatter) and selected_trace.mode == 'lines':
# #                     selected_trace.line.color = 'black'
# #                     selected_trace.line.width = 10
# #                     selected_values = df.iloc[selected_trace_index].values
# #                     x_labels = [f'f{i+1}' for i in range(len(selected_values))]
# #                     selected_trace.text = '<br>'.join([
# #                         f'{label}: {value: .2f}'
# #                         for label, value in zip(x_labels, selected_values)
# #                     ])
# #                     selected_trace.hoverinfo = 'text'
# #                     for i, trace in enumerate(fig.data):
# #                         if isinstance(
# #                                 trace, go.Scatter
# #                         ) and trace.mode == 'lines' and i != selected_trace_index:
# #                             trace.line.color = 'rgb(203, 195, 227)'
# #                             trace.opacity = 0.2

# #                 highlighted_trace = go.Scatter(x=[f1_point],
# #                                 y=[f2_point],
# #                                 mode='lines+markers',
# #                                 line=dict(color='black', width=30),
# #                                 marker=dict(color='black', size=30),
# #                                 hoverlabel=dict(font_size=28),
# #                                 hovertemplate=None,
# #                                 hoverinfo='text',
# #                                 text='<br>'.join([
# #                         f'{label}: {value: .2f}'
# #                         for label, value in zip([f1_point], [f2_point])
# #                     ]),
# #                                 name="")
# #                 fig.update_traces(visible= True)
# #                 highlighted_index = None
# #                 for i, trace in enumerate(fig.data):
# #                     if instance(trace, go.Scatter) and trace.mode == 'lines+markers':
# #                         highlighted_index = i
# #                         break

# #                 if highlighted_index is not None:
# #                     fig.data.pop(highlighted_index)

# #                 fig.add_trace(highlighted_trace)

# #                 if selected_data:
# #                     for point in selected_data['points']:
# #                         selected_trace_index = point['curveNumber']
# #                         if selected_trace_index != highlighted_index:
# #                             selected_trace = fig.data[selected_trace_index]
# #                             selected_trace.opacity = 1.0
# #                             selected_trace.line.color = 'black'

#             # elif isinstance(fig.data[0], go.Parcoords):
#             #     coords = [
#             #         click_data['points'][0]['dimension_values'][i]
#             #         for i in range(len(data[0]))
#             #     ]
#             #     dimensions = [{
#             #         "label": f"Objective {i+1}",
#             #         "values": [coords[i]]
#             #     } for i in range(len(coords))]
#             #     if len(fig.data) == 1:
#             #         fig.add_trace(
#             #             go.Parcoords(line=dict(color='LightSeaGreen', size=30),
#             #                          dimensions=dimensions))
#             #     else:
#             #         fig.data[1].dimensions = dimensions

#     fig.update_layout(showlegend=False)
#     return fig


@app.callback([
    Output("mop-objective-graph", "figure"),
    Output("mop-decision-graph", "figure")
], Input("tests", "value"))
def update_mop_graphs(test_selection):
    if test_selection == 'DTLZ1':
        n_var_obj = 7  # Number of decision variables
        n_obj = 2  # Number of objectives

        # Get the DTLZ1 problem from pymoo
        problem_obj = get_problem("dtlz1", n_var=n_var_obj, n_obj=n_obj)

        # Define the grid resolution
        GRID_RESOLUTION = 100
        grid = np.linspace(0.0, 1.0, GRID_RESOLUTION)

        # List to store all solutions and their objectives
        solutions_obj = []
        objectives = []

        for x1 in grid:
            for x2 in grid:
                # Create a solution with the current grid coordinates
                solution = np.array([x1, x2] + [0.5] * (problem_obj.n_var - 2))
                # Evaluate the solution to get the objectives
                f = problem_obj.evaluate(solution, return_values_of=["F"])
                # if any(np.isinf(f)) or any(np.isnan(f)):
                #     f = np.ones_like(f) * 1e6
                # Store the solution and its objectives
                solutions_obj.append(solution)
                objectives.append(f)

# Convert the lists to numpy arrays
        solutions_obj = np.array(solutions_obj)
        objectives = np.array(objectives)
        # normalized_objectives = objectives / np.max(objectives)
        # Perform non-dominated sorting to get the Pareto fronts
        # fronts = NonDominatedSorting().do(objectives,
        #                                   only_non_dominated_front=False)

        # Assign the Pareto rank to each solution as its cost
        # for rank, front in enumerate(fronts, start=1):
        #     avg_objectives = np.mean(normalized_objectives[front], axis=0)
        #     for idx in front:
        #         i, j = divmod(idx, GRID_RESOLUTION)
        #         cost_landscape[i, j] = np.mean(avg_objectives)

        objective_fig = go.Figure(data=[
            go.Scatter(x=objectives[:, 0],
                       y=objectives[:, 1],
                       mode='markers',
                       marker=dict(size=2))
        ])
        objective_fig.update_layout(
            xaxis_title='Objective 1',
            yaxis_title='Objective 2',
            xaxis = dict(showgrid=False, zeroline=True, zerolinecolor='black', showline=True,linecolor='black', gridwidth=1, title_font=dict(size=20, color='black')),
            yaxis = dict(showgrid=False, zeroline=True, zerolinecolor='black', showline=True,linecolor='black', gridwidth=1, title_font=dict(size=20, color='black')),
            # paper_bgcolor='rgb(0,0,0,0)',
            plot_bgcolor='white',
        )
        objective_fig.update_traces(
            hovertemplate='f1: %{x}<br>f2: %{y}<br><extra></extra>')

        n_var = 2  # Number of decision variables
        n_obj = 2  # Number of objectives

        # Get the DTLZ1 problem from pymoo
        problem = get_problem("dtlz1", n_var=n_var, n_obj=n_obj)

        # Define the grid resolution
        GRID_RESOLUTION = 100
        grid_x = np.linspace(0.0, 1.0, GRID_RESOLUTION)
        grid_y = np.linspace(0.0, 1.0, GRID_RESOLUTION)
        # Generate the cost landscape

        cost_landscape = np.full((GRID_RESOLUTION, GRID_RESOLUTION), np.inf)

        # List to store all solutions and their objectives
        solutions = []
        objectives = []

        for i, x1 in enumerate(grid_x):
            for j, x2 in enumerate(grid_y):
                # Create a solution with the current grid coordinates
                solution = np.array([x1, x2] + [0.5] * (n_var - n_obj))
                # Evaluate the solution to get the objectives
                f = problem.evaluate(solution)
                if any(np.isinf(f)) or any(np.isnan(f)):
                    f = np.ones_like(f) * 1e6
        # Store the solution and its objectives
                solutions.append(solution)
                objectives.append(f)

# Convert the lists to numpy arrays
        solutions = np.array(solutions)
        objectives = np.array(objectives)
        normalized_objectives = objectives / np.max(objectives)
        # Perform non-dominated sorting to get the Pareto fronts
        fronts = NonDominatedSorting().do(objectives,
                                          only_non_dominated_front=False)

        # Assign the Pareto rank to each solution as its cost
        for rank, front in enumerate(fronts, start=1):
            avg_objectives = np.mean(normalized_objectives[front], axis=0)
            for idx in front:
                i, j = divmod(idx, GRID_RESOLUTION)
                cost_landscape[i, j] = np.mean(avg_objectives)

        decision_fig = go.Figure(data=[
            go.Heatmap(
                z=cost_landscape.T, x=grid_x, y=grid_y, colorscale="Viridis")
        ])
        decision_fig.update_layout(xaxis_title='Decision Variable 1',
                                   yaxis_title='Decision Variable 2',xaxis = dict(title_font=dict(size=20, color='black')),
            yaxis = dict(title_font=dict(size=20, color='black')),
                                  )
        decision_fig.update_traces(
            hovertemplate='x1: %{x}<br>x2: %{y}<br><extra></extra>')
        return objective_fig, decision_fig

    elif test_selection == 'Aspar':

        def aspar(x):
            x1, x2 = x
            if x1 == 0:
                x1 = 1e-10
            if x2 == 0:
                x2 = 1e-10
            f1 = x1**4 - 2 * x1**2 + 2 * x2**2 + 1
            f2 = (x1 + 0.5)**2 + (x2 - 2)**2
            return np.array([f1, f2])

# Define the grid resolution

        GRID_RESOLUTION = 100
        grid_x = np.linspace(-2.0, 2.0, GRID_RESOLUTION)
        grid_y = np.linspace(-2.0, 2.0, GRID_RESOLUTION)

        # Generate the cost landscape
        cost_landscape = np.full((GRID_RESOLUTION, GRID_RESOLUTION), np.inf)

        # List to store all solutions and their objectives
        solutions = []
        objectives = []

        for i, x1 in enumerate(grid_x):
            for j, x2 in enumerate(grid_y):
                # Create a solution with the current grid coordinates
                solution = np.array([x1, x2])
                # Evaluate the solution to get the objectives
                f = aspar(solution)
                # Store the solution and its objectives
                solutions.append(solution)
                objectives.append(f)


# Convert the lists to numpy arrays
        solutions = np.array(solutions)
        objectives = np.array(objectives)
        normalized_objectives = objectives / np.max(objectives)

        # Perform non-dominated sorting to get the Pareto fronts
        fronts = NonDominatedSorting().do(objectives,
                                          only_non_dominated_front=False)

        # Assign the Pareto rank to each solution as its cost
        for rank, front in enumerate(fronts, start=1):
            avg_objectives = np.mean(normalized_objectives[front], axis=0)
            for idx in front:
                i, j = divmod(idx, GRID_RESOLUTION)
                # cost_landscape[i, j] = rank
                cost_landscape[i, j] = np.mean(avg_objectives)
        objective_fig = go.Figure(data=[
            go.Heatmap(
                z=cost_landscape.T, x=grid_x, y=grid_y, colorscale="Viridis")
        ])
        objective_fig.update_layout(xaxis_title='f1',
                                    yaxis_title='f2',
                                    scene=dict(
                                        xaxis=dict(title='f1',
                                                   title_font=dict(size=32)),
                                        yaxis=dict(title='f2',
                                                   title_font=dict(size=28)),
                                        zaxis=dict(title='Cost',
                                                   title_font=dict(size=28)),
                                    ))
        objective_fig.update_traces(
            hovertemplate='f1: %{x}<br>f2: %{y}<br><extra></extra>')
        decision_fig = go.Figure(data=[
            go.Heatmap(
                z=cost_landscape.T, x=grid_x, y=grid_y, colorscale="Viridis")
        ])
        decision_fig.update_layout(xaxis_title='x1',
                                   yaxis_title='x2',
                                   scene=dict(
                                       xaxis=dict(title='x1',
                                                  title_font=dict(size=28)),
                                       yaxis=dict(title='x2',
                                                  title_font=dict(size=28)),
                                       zaxis=dict(title='Cost',
                                                  title_font=dict(size=28)),
                                   ))
        decision_fig.update_traces(
            hovertemplate='x1: %{x}<br>x2: %{y}<br><extra></extra>')
        return objective_fig, decision_fig

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=5001)
