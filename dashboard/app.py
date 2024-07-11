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
import plotly.express as px
from dashlib.layout import interface_layout
from dashlib.components import gen_graph, blank_figure
from data.parser import parse_data
from logger.custom import NumpyEncoder
from dash.exceptions import PreventUpdate
from pymoo.optimize import minimize
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
from sklearn.cluster import KMeans

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

def generate_data_dtlz1(n_var, n_obj,obj_weights):
    problem = get_problem('dtlz1', n_var=n_var, n_obj=n_obj)
    algorithm = NSGA2(pop_size=300)
    res = minimize(problem, algorithm, ('n_gen', 300), seed=1, verbose=False)

    X = res.X
    F = res.F
    print(f"Original objective function values (F): \n{F}")
    weighted_F = F * np.array(obj_weights)
    print(f"Weighted objective function values: \n{weighted_F}")
    n_var = problem.n_var
    n_obj = problem.n_obj
    var_cols = [f'x{i}' for i in range(1, n_var + 1)]
    obj_cols = [f'f{i}' for i in range(1, n_obj + 1)]
    df = pd.DataFrame(X, columns=var_cols)
    for i in range(n_obj):
        df[obj_cols[i]] = weighted_F[:, i]

    # front = res.F
    # print("Generated Data: ")
    # print(df.head())
    return df

def generate_data_dtlz3(n_var, n_obj, obj_weights):
    problem = get_problem('dtlz3', n_var=n_var, n_obj=n_obj)
    algorithm = NSGA2(pop_size=300)
    res = minimize(problem, algorithm, ('n_gen', 300), seed=1, verbose=False)

    X = res.X
    F = res.F
    weighted_F = F * np.array(obj_weights)
    n_var = problem.n_var
    n_obj = problem.n_obj
    var_cols = [f'x{i}' for i in range(1, n_var + 1)]
    obj_cols = [f'f{i}' for i in range(1, n_obj + 1)]
    df = pd.DataFrame(X, columns=var_cols)
    for i in range(n_obj):
        df[obj_cols[i]] = weighted_F[:, i]

    # front = res.F
    # print("Generated Data: ")
    # print(df.head())
    return df

@app.callback(
    Output("num-decision-vars", "value"),
    Output("num-objective-vars", "value"),
    Input("test-dropdown", "value"),
)
def toggle_inputs(test):
    if test == "RealTimeData" or test == "RealTimeData2":
        return 2, 2
    return False, False

@app.callback(
    Output("data-generated", "data", allow_duplicate=True),
    [Input("test-dropdown", "value")], prevent_initial_call=True
)
def generate_data_real_time(test):
    if test == "RealTimeData":
        df = pd.read_csv('real_time_data.csv')
        return df.to_json(orient='records')
    elif test == "RealTimeData2":
        df = pd.read_csv('real_time_data2.csv')
        return df.to_json(orient='records')
    else:
        raise dash.exceptions.PreventUpdate
    # print(df.head())
    # decision_variables = [col for col in df.columns if col.startswith('x')]
    # objective_variables = [col for col in df.columns if col.startswith('f')]

    # data_records = []

    # for index, row in df.iterrows():
    #     data_record ={'x': [], 'f': []}
    #     for var in decision_variables:
    #         data_record['x'].append(row[var])
    #     for var in objective_variables:
    #         data_record['f'].append(row[var])
    #     data_records.append(data_record)

    # return json.dumps(data_records)



app.layout = html.Div([
    dcc.Store(id="slider-values-store", data={}),
    dcc.Store(id="slider-change-status", data=False),
    dcc.Store(id="df-dimensions", data={}),
    dcc.Store(id='decision-variables-store', data={}),
    dcc.Store(id="decision-values-store", data=[]),
    dcc.Store(id='selected-radar-pts-store', data=[]),
    dcc.Store(id='selected-obj-pts-store', data=[]),
    dcc.Store(id='temp-summary-min-max', data=[]),
    interface_layout,
    html.Div(id="radar-sliders", style={'display': 'none'}),
    dcc.Loading(id='loading-2', children=[dcc.Graph(id="radar-chart", style={'display': 'none'})], target_components={'radar-chart': 'figure'}),
    dcc.Store(id='obj-weights-store',data=[])
])


@app.callback([Output("data-generated", "data"),
              Output('obj-weights-store','data'),
              Output('graph1','figure'),
            #   Output('update-message','children')
              ],
              [Input("generated-dtlz-button", "n_clicks"), Input('obj-weights-input','value')], [
                  State("num-decision-vars", "value"),
                  State("num-objective-vars", "value"),
                  State("test-dropdown", "value"),
              ],prevent_initial_callbacks='initial_duplicate')
def generate_data_callback(n_clicks, obj_weights_input, n_var, n_obj, test):
    if n_var is None or n_obj is None:
        # return "", [], blank_figure(),"Please enter number of variables" 
        raise dash.exceptions.PreventUpdate("Please enter number of variables")
    if n_clicks is None:
        # return "", [], blank_figure(),""
        raise PreventUpdate

    if test in ['DTLZ1', 'DTLZ3']:
        if obj_weights_input:
            obj_weights = [float(x) for x in obj_weights_input.split(',') if x.strip()]
            # obj_weights = [float(obj_weights)] * n_obj
            # obj_weights = list(map(float,obj_weights_input.split(',')))
            # if len(obj_weights) != n_obj:
            #     return "",[], blank_figure(),f"Number of weights provided ({len(obj_weights)}) does not match the number of objectives ({n_obj})."
        else:
            obj_weights = [1.0] * n_obj
        print(f"Objective weights:{obj_weights}")
    if test == 'DTLZ1':
        df_generated = generate_data_dtlz1(n_var=n_var, n_obj=n_obj, obj_weights=obj_weights)
    elif test == 'DTLZ3':
        df_generated = generate_data_dtlz3(n_var=n_var, n_obj=n_obj, obj_weights=obj_weights)
    elif test == 'RealTimeData':
         df_generated = generate_data_real_time()
        # df_generated, decision_variables, objective_variables = generate_data_real_time()
        # return df_generated.to_json(orient='records')
    elif test == 'RealTimeData2':
         df_generated = generate_data_real_time()
    else:
        raise PreventUpdate
    print(f"Generated Data:\n{df_generated}")
    fig = gen_graph(df_generated)
    return df_generated.to_json(orient='records'),obj_weights, fig
    # filename = "data_generated.json"
    
    # print("Generated JSON: ",df_generated.to_json(orient='records'))
    # return df_generated.to_json(orient='records'),obj_weights, fig,"Graph updated successfully"


@app.callback(
    Output('stored-df', 'data'),
    Output('use-cluster-toggle', 'style'),
    Output('cluster-dropdown', 'style'),
    Output('cluster-dropdown', 'options'),
    Output("summary-table", 'style'),
    Output("summary-table", 'children'),
    Output('obj-help', 'children'),
    Output('df-dimensions', 'data'),
    Output('decision-variables-store', 'data'),
    Output('decision-values-store', 'data'),
    Output('selected-obj-pts-store', 'data'),
    Output('selected-radar-pts-store', 'data'), 
    Output('graph1', 'clickData'),
    Output('graph1', 'selectedData'),
    [
      Input('upload-data', 'contents'),
      Input('upload-data', 'filename'),
      Input("data-generated", "data"),
      Input('use-cluster-toggle', 'value'),
    ],
    prevent_initial_call=True)
def update_summary(contents, filename, generated_data, cluster_switch):
    print('update_summary')
    
    if generated_data:
        generated_data_io = io.StringIO(generated_data)
        df = pd.read_json(generated_data_io, orient='records')
    elif contents is None:
        return [], {'display': 'none'}, {'display': 'none'}, [], {'display': 'none'}, [], dash.no_update, {}, [], dash.no_update, [], [], {}, {}
    else:
        #parse the uploaded file
        content_type, content_string = contents[0].split(',')
        decoded = base64.b64decode(content_string)
        # if 'csv' in filename.lower():
        #     file = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        # else:
        file = json.loads(decoded)

        df = pd.DataFrame(file)

    decision_variables = [col for col in df.columns if col.startswith('x') or col.startswith('B')]
    objective_functions = [col for col in df.columns if col.startswith(('f','T','P'))]
    
    help_text = 'Click and drag to select an area containing the points to filter.'
    
    if 'cluster' in cluster_switch:
        X = df[objective_functions].values
        kmeans = KMeans(n_clusters=len(objective_functions), random_state=0, n_init="auto").fit(X)
        df['labels'] = kmeans.labels_
        options_list = []
        tmp_colors = px.colors.qualitative.Plotly
        colors_dict = {}
        for i, x in enumerate(sorted(df.labels.unique())):
            options_list.append({
                'label': html.Div([ 
                    html.Div(style={'width': '15px', 'height': '15px', 'background': tmp_colors[i]}),
                    html.Div(x, style={'marginLeft': '3px'})
                ], style={'display': 'flex', 'alignItems': 'center'}), 
                'value': x}
            )
        help_text = 'Select cluster(s) on the dropdown or click and drag to select an area containing the points to filter.'

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
    
    return df.to_dict(orient='records'), {'display': 'block'} if len(objective_functions) >= 4 else {'display': 'none'},{'display': 'block', 'width': '10vw'} if 'cluster' in cluster_switch else {'display': 'none'}, options_list if 'cluster' in cluster_switch else [], {
        'margin': '10rem auto auto auto',
        'fontWeight': '500',
        'borderRadius': '10px',
        'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.8)',
        'padding': '1.7rem',
        'fontFamily': 'Arial, Helvetica, sans-serif',
        'textAlign': 'center',
        'width': '82%'
    }, summary_table, help_text, {'obj': len(objective_functions), 'dec': len(decision_variables)}, decision_variables, [[0]]*len(decision_variables), [], [], {}, {}

@app.callback(
    Output('temp-summary-min-max', 'data'),
    Input('decision-values-store', 'data'),
    State('decision-variables-store', 'data'),
    State({
        "type": "dec-sliders",
        "index": ALL
    }, "value"),
    State({
        "type": "dec-sliders",
        "index": ALL
    }, "id"),
)

def temp_callback(dec_values, dec_vars, slider_values, slider_ids):
    filtered_indices = [dec_vars.index(f"x{slider_id['index'].split('rad-slider-')[1]}") for slider_id in slider_ids]
    filtered_values = {}
    for i, k in enumerate(filtered_indices):
        filtered_values[dec_vars[k]] = slider_values[i]

    changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
    merged = {}
    for i, var in enumerate(dec_vars):
        values = [solution[i] for solution in dec_values if (len(solution) >= len(dec_vars))]
        if len(values) > 0:
            minimum = min(values)
            maximum = max(values)
            if var in filtered_values:
                minimum = filtered_values[var][0]
                maximum = filtered_values[var][1]
            merged[var] = {'min': minimum, 'max': maximum}
#     print('merged output', merged)
    return merged

# Clean up update_output callback function
@app.callback(
    Output('graph1', 'figure', allow_duplicate=True),
    Output('sliders', 'children'),
    Input('stored-df', 'data'),
    Input('selected-obj-pts-store', 'data'),
    Input('selected-radar-pts-store', 'data'),
    Input({
        "type": "ds-sliders",
        "index": ALL
    }, "value"),
    Input({
        "type": "dec-sliders",
        "index": ALL
    }, "value"),
    Input('temp-summary-min-max', 'data'),
    Input('decision-values-store', 'data'),
    Input('use-cluster-toggle', 'value'),
    State('df-dimensions', 'data'),
    State('decision-variables-store', 'data'),
    State('graph1', 'figure'),
    State('radar-chart', 'figure'),
    State('test-dropdown', 'value'),
    State('graph1', 'selectedData'),
    prevent_initial_call=True
)

def clean_callback(data, obj_pts_store, radar_pts_store, ds_slider_values, filtered_dec, dec_range_store, dec_values, use_cluster, dims, dec_vars,
                   curr_fig, curr_rad_fig, test, selected_data):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
#     print('clean_callback', changed_id, use_cluster)

    if data is None:
        raise PreventUpdate
    else:
        df = pd.DataFrame(data)
        objective_functions = [col for col in df.columns if col.startswith(('f','T','P'))]
        fig = gen_graph(df, 'cluster' in use_cluster)
        

        if ('stored-df.data' in changed_id) | (len(obj_pts_store) == 0) | ('use-cluster-toggle.value' in changed_id):
            
            fig = gen_graph(df, 'cluster' in use_cluster)
            print('stored-df.data changed or obj_pts_store is NONE')
            if dims['dec'] < 5:
                sliders = []
                for var, (min_val, max_val) in zip(dec_vars, [(0, 1)] * len(dec_vars)):
                    if test == 'RealTimeData' or test == 'RealTimeData2':
                        min_val, max_val = 5, 20
                        step = 5
                        # marks ={i: f'{i: .2f}' for i in np.arange(min_val, max_val + 1, step)}
                    # else:
                        # step=0.01,
                        # marks={i: f'{i: .2f}'
                        #         for i in np.arange(min_val, max_val + 0.1, 0.25)
                        #             },
                        sliders.append(
                            html.Div(
                                [
                                    html.Label(id=f'{var}',
                                               children=f'{var}',
                                               style=labelFlex,
                                               className="slider-label"),
                                    dcc.RangeSlider(
                                        id={'type': 'ds-sliders', 'index': f'slider-{var}'},
                                        min=min_val,
                                        max=max_val,
                                        step=0.01,
                                        # marks=marks,
                                        marks={i: f'{i: .2f}' for i in np.arange(min_val, max_val + 0.5, 3.75)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                        className="slider-5",
                                    )
                                ],
                                style={
                                    'display': 'flex',
                                    'alignItems': 'center',
                                    'width': '100%',
                                },
                            )
                        )
                    else:
                        sliders.append(
                            html.Div(
                                [
                                    html.Label(id=f'{var}',
                                               children=f'{var}',
                                               style=labelFlex,
                                               className="slider-label"),
                                    dcc.RangeSlider(
                                        id={'type': 'ds-sliders', 'index': f'slider-{var}'},
                                        min=min_val,
                                        max=max_val,
                                        step=0.01,
                                        # marks=marks,
                                        marks={i: f'{i: .2f}' for i in np.arange(min_val, max_val + 0.1, 0.25)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                        className="slider-5",
                                    )
                                ],
                                style={
                                    'display': 'flex',
                                    'alignItems': 'center',
                                    'width': '100%',
                                },
                            )
                        )
                default = html.Div([
                    html.Div(sliders),
                    dcc.Graph(id='radar-chart', style={'display': 'none'}),
                    html.Div(id='radar-sliders', style={'display': 'none'})   
                ])
                return fig, default
#                 return fig, html.Div(sliders, style={
#                     'display': 'flex',
#                     'flexDirection': 'column',
#                     'alignItems': 'center',
#                     'width': '100%',
#                     'padding': '2%',
#                     'position':'relative',
#                     'top':'27%'
#                 })
            else:
                rad_sliders = []
                default_r = [0] * len(dec_vars)
                default_th = list(dec_vars)

                for x in range(len(default_r)):
                    rad_sliders.append(
                        html.Div(
                            [
                                html.P(f"x{x+1}", style={'fontSize': '18px'}),
                                dcc.Slider(
                                    id={'type': 'dec-sliders', 'index': f'rad-slider-{x+1}'},
                                    min=0,
                                    max=1,
                                    step=0.01,
                                    marks=new_markers,
                                    tooltip={"placement": "bottom","always_visible": True},
                                    value=default_r[x],
                                    className='slider-5'
                                )
                            ],
                            style={
                                'display': 'flex',
                                'alignItems': 'center',
                                'width': '100%',
                            }
                        )
                    )
                    
                rad_fig = go.Figure(data=go.Scatterpolar(r=default_r, theta=default_th, line_color='MediumPurple'))
                rad_fig.update_layout(
                    font=dict(size=16, color='black'),
                    polar = dict(
                        radialaxis = dict(range=[0, max(list(map(max, dec_values)))+0.1], showticklabels=False, ticks='')
                    ),
                    template=None, dragmode='select', margin=dict(l=30, r=30, t=40, b=45))

                return fig, html.Div(
                    [
                        dcc.Graph(id='radar-chart', figure=rad_fig,
                                  style={'width': '95%', 'height': '100%'}
                                 ),
                        html.Div(id='radar-sliders', style={'display': 'none'}),
                    ],
                    style={
                        'display': 'flex',
                        'flexDirection': 'column',
                        'alignItems': 'center',
                        'justifyContent': 'space-between'
                    }
                )

                
        if ('selected-obj-pts-store.data' in changed_id) | (('decision-values-store.data' in changed_id) & (any('slider' in t for t in changed_id) == False)):
#             print('obj_pts_store', obj_pts_store)
            if obj_pts_store:
                if dims['obj'] < 3:
                    active_pts = [pt['pointNumber'] for pt in obj_pts_store['points']]
                else:
                    active_pts = [pt['curveNumber'] for pt in obj_pts_store['points']]
#                     print('active_pts', active_pts, len(active_pts))
                    for d in fig['data']:
                        name = int(d['name'])
                        if 'cluster' not in use_cluster:
                            if name not in active_pts:
                                d['line']['color'] = 'rgba(147,112,219, 0.05)'
                            else:
                                d['line']['color'] = 'rgba(147,112,219, 1)'
                        else:
                            h = d['line']['color'].strip('#')
                            r, g, b = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                            if name not in active_pts:
                                d['line']['color'] = f"rgba({r}, {g}, {b}, 0.05)"
                            else:
                                d['line']['color'] = f"rgba({r}, {g}, {b}, 1)"

#                 print('selected_data', selected_data)

                if 'range' in obj_pts_store:
                    ranges = obj_pts_store['range']
                    selection_bounds = {
                        "x0": ranges["x"][0],
                        "x1": ranges["x"][1],
                        "y0": ranges["y"][0],
                        "y1": ranges["y"][1],
                    }

                    fig.add_shape(
                        dict(
                            {"type": "rect", "line": {"width": 1.5, "dash": "dot", "color": "black"}},
                            **selection_bounds
                        )
                    )

                fig.update_traces(selectedpoints=active_pts)
                
            if dims['dec'] < 5:
                print('return fig here')
                return fig, dash.no_update
            else:
                rad_fig = go.Figure()
                if len(dec_values) > 0:
                    merged = {}
                    new_th = dec_vars.copy()
                    new_th.append(dec_vars[0])
                    
                    for i, var in enumerate(dec_vars):
                        values = [solution[i] for solution in dec_values if len(solution) == len(dec_vars)]
                        if len(values) > 0:
                            merged[var] = {'min': min(values), 'max': max(values)}

#                     if len(merged) > 0:
#                         rad_fig.add_trace(go.Scatterpolar(r=[merged[x]['min'] for x in new_th] , theta=new_th, fill='toself', mode='lines', name='Min solutions'))
#                         rad_fig.add_trace(go.Scatterpolar(r=[merged[x]['max'] for x in new_th], theta=new_th, fill='toself', mode='lines', name='Max solutions')) 
                    
                    for solution in dec_values:
                        new_r = solution
                        new_r.append(new_r[0])
#                         print('new_r', new_r, new_th)
                        rad_fig.add_trace(go.Scatterpolar(r=new_r, theta=new_th, line_color='MediumPurple'))
                
                rad_fig.update_layout(
                    font=dict(size=16, color='black'),
                    template=None,
                    showlegend=False, dragmode='select', margin=dict(l=40, r=40, t=40, b=45),
                    polar = dict(
                        radialaxis = dict(range=[0, max(list(map(max, dec_values)))+0.1], showticklabels=False, ticks='')
                    )
                )

                if radar_pts_store:
                    raise PreventUpdate
                else:
                    return fig, html.Div([
                            html.Div([
                                dcc.Graph(id='radar-chart', figure=rad_fig, style={'width': '95%', 'height': '95%'}),
                                html.Div(id='radar-sliders', style={'display': 'none'})
                            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'width': '100%', 'height': '100%'})
                        ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'space-between'})

#         slider changes -> filter active solutions on graph1  
        if (('slider' in changed_id[0]) & (len(changed_id) == 1)) | (all('slider' in t for t in changed_id)) | (('temp-summary-min-max.data' in changed_id ) & (any('slider' in t for t in changed_id))):
            dec_slider_values = [list(x.values()) for x in dec_range_store.values()]

            slider_vals = ds_slider_values
            if any('dec-slider' in v for v in changed_id):
                if list(curr_rad_fig['layout'].keys())[-1] != 'template':
                    raise PreventUpdate
                slider_vals = dec_slider_values

            # updated_slider ex) {'x1': [0, 0.6], 'x2': [0.2, 0.4], ...}
            updated_slider = {}
            for i, val in enumerate(slider_vals):
                updated_slider[dec_vars[i]] = [float(v) for v in val]
#             print('updated_slider', updated_slider)

            trace_indices = [x['curveNumber'] for x in obj_pts_store['points']]
            subset = df.loc[trace_indices, dec_vars].astype(float)
            new_solutions = []
#             for idx, d in enumerate(subset.values.tolist()):
            for idx, row in subset.iterrows():
                d = row.values
                statuses = []
                for k, v in updated_slider.items():
                    i = dec_vars.index(k)
                    statuses.append((float(d[i]) >= v[0]) & (float(d[i]) <= v[1]))
                if sum(statuses) == len(dec_vars):
                    new_solutions.append(idx)
#             print('new_solutions', len(new_solutions), new_solutions)
#             print('check dec values', len(dec_values), dec_values)

            new_fig = go.Figure(curr_fig)
            if dims['obj'] < 3:
                new_fig.update_traces(selectedpoints=new_solutions)
            else:
                for d in new_fig['data']:
                    name = int(d['name'])
                    if 'cluster' not in use_cluster:
                        if name not in new_solutions:
                            d['line']['color'] = 'rgba(147,112,219, 0.1)'
                        else:
                            d['line']['color'] = 'rgba(147,112,219, 1)'
            
                    else:
                        r, g, b, a = d['line']['color'].strip('rgba').replace('(', '').replace(')', '').replace(' ', '').split(',')
                        if name not in new_solutions:
                            d['line']['color'] = f"rgba({r}, {g}, {b}, 0.05)"
                        else:
                            d['line']['color'] = f"rgba({r}, {g}, {b}, 1)"
                    
            return new_fig, dash.no_update

        # PLACEHOLDER
        raise PreventUpdate


@app.callback(Output('radar-chart', 'figure', allow_duplicate=True),
              Output('slider-change-status', 'data', allow_duplicate=True),
              Output('decision-values-store', 'data', allow_duplicate=True),
              Output('no-data-alert', 'is_open', allow_duplicate=True),
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

def update_radar_from_slider(slider_values, fig, dec_values, dec_vars, radar_pts, obj_pts, data, dims):
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

            if obj_pts['points']:
                df = pd.DataFrame(data)
                if dims['obj'] < 3:
                    trace_indices = [
                        obj['pointNumber'] for obj in obj_pts["points"]
                    ]
                else:
                    trace_indices = [
                        obj['curveNumber'] for obj in obj_pts["points"]
                    ]
                subset = df.iloc[trace_indices, :len(dec_vars)].astype(float)

            curr_data = fig['data'].copy()
            updated_slider = {}
            for i, th in enumerate(filtered_th):
                updated_slider[th] = slider_values[i]

            area_obj = [d for d in curr_data if 'name' in d]

            curr_solutions = [{
                'r': el.copy() + [el[0]],
                'theta': dec_vars.copy() + [dec_vars[0]],
                'type': 'scatterpolar',
                'line_color': 'MediumPurple',
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
#             print('solutions size in radar chart', len(solutions))
            fig['data'] = filtered_data
            if len(solutions) > 0:
                return fig, True, [sol['r'] for sol in solutions], False
            else:
                return dash.no_update, dash.no_update, dash.no_update, True

        raise PreventUpdate
    raise PreventUpdate


@app.callback(Output('selected-radar-pts-store', 'data', allow_duplicate=True),
              Output('selected-obj-pts-store', 'data', allow_duplicate=True),
              Output('dec-help', 'children'),
              Input('radar-chart', 'selectedData'),
              Input({
                  "type": "dec-sliders",
                  "index": ALL
              }, "value"),
              Input('graph1', 'clickData'),
              Input('graph1', 'selectedData'),
              Input('cluster-dropdown', 'value'),
              State('decision-variables-store', 'data'),
              State('selected-obj-pts-store', 'data'),
              State('graph1', 'figure'),
              State('stored-df', 'data'),
              prevent_initial_call=True)

def save_selection(radar_selected, dec_sliders, click_data, selected_data, selected_cluster, dec_vars, curr_obj_pts, fig, stored_data):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
#     print('save_selection', changed_id)

    if len(dec_vars) >= 5:
        if 'rad-slider-' in changed_id[0]:
            raise PreventUpdate
        if 'graph1.clickData' in changed_id:
            return None, click_data, dash.no_update
        if changed_id[0] == 'graph1.selectedData':
            if selected_data:
                if len(selected_data['points']) == 0:
                    raise PreventUpdate
                return None, selected_data, 'Click and drag to draw a box around the area containing the points to filter. (The box should contain points, not just lines.)'
            return None, {}, 'Click and drag to draw a box around the area containing the points to filter. (The box should contain points, not just lines.)'
        if 'cluster-dropdown.value' in changed_id:
            if selected_cluster:
                df = pd.DataFrame(stored_data)
                selected_obj = {}
                selected_obj['points'] = [{'curveNumber': x} for x in list(df[df.labels.isin(selected_cluster)].index)]
                return None, selected_obj, dash.no_update
            return None, {}, dash.no_update
        return radar_selected, dash.no_update, dash.no_update
    else:
        if 'graph1.clickData' in changed_id:
            print('clickdata', click_data)
            return None, click_data, dash.no_update
        if changed_id[0] == 'graph1.selectedData':
            if selected_data:
                if len(selected_data['points']) == 0:
                    print('Check here', selected_data)
                    raise PreventUpdate
                return None, selected_data, 'Move the sliders to modify the values of decision variables.'
            return None, {}, 'Move the sliders to modify the values of decision variables.'
        if 'cluster-dropdown.value' in changed_id:
            if selected_cluster:
                df = pd.DataFrame(stored_data)
                selected_obj = {}
                selected_obj['points'] = [{'curveNumber': x} for x in list(df[df.labels.isin(selected_cluster)].index)]
                return None, selected_obj, dash.no_update
            return None, {}, dash.no_update
        raise PreventUpdate


@app.callback(Output('radar-sliders', 'children'),
              Output('radar-sliders', 'style'),
              Output('radar-chart', 'style'),
              Output('radar-chart', 'figure', allow_duplicate=True),
              Output('dec-help', 'children', allow_duplicate=True),
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
                   dec_values, decision_vars, pc_fig):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
    if selected_radar_values:
        filtered_vars = sorted(list(
            set([obj['theta'] for obj in selected_radar_values['points']])),
                               key=lambda x: int(x.split('x')[1]))
        filtered_indices = [decision_vars.index(x) for x in filtered_vars]
        
        new_sliders = []
        for v in filtered_vars:
            idx = decision_vars.index(v)
            val = [
                min([values[idx] for values in dec_values]),
                max([values[idx] for values in dec_values])
            ]
            if ('rad-slider' in changed_id[0]) | (changed_id[0] == 'radar-chart.figure'):

                i = filtered_vars.index(v)
                val = [dec_slider_values[i][0], dec_slider_values[i][1]]

            new_sliders.append(
                html.Div(
                    [
                        html.P(f"{v}", style={'fontSize': '18px'}),
                        dcc.RangeSlider(
                            id={'type': 'dec-sliders', 'index': f'rad-slider-{decision_vars.index(v)+1}'},
                            min=0,
                            max=1,
                            step=0.01,
                            marks=new_markers,
                            tooltip={"placement": "bottom", "always_visible": True},
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
                              margin=dict(l=30, r=30, t=30, b=30))
        return new_sliders, {'display': 'block', 'width': '45%'}, {'width': '50%', 'height': '100%'}, rad_fig, 'Move the sliders to modify the values of filtered variables and double-click on an empty area in the chart to deselect.', dash.no_update
    else:
        if len(decision_vars) >= 5:
            th = decision_vars
            th.append(decision_vars[0])

            rad_fig = go.Figure()
#             if len(summary) > 0:
#                 rad_fig.add_trace(
#                     go.Scatterpolar(r=[summary[x]['min'] for x in th],
#                                     theta=th,
#                                     fill='toself',
#                                     mode='lines',
#                                     name='Minimum'))
#                 rad_fig.add_trace(
#                     go.Scatterpolar(r=[summary[x]['max'] for x in th],
#                                     theta=th,
#                                     fill='toself',
#                                     mode='lines',
#                                     name='Maximum'))
            for solution in dec_values:
                r = solution
                r.append(r[0])
                rad_fig.add_trace(go.Scatterpolar(r=r, theta=th, line_color='MediumPurple'))

            rad_fig.update_layout(font=dict(size=16, color='black'), template=None, showlegend=False,
                                  dragmode='select',
                                  margin=dict(l=30, r=30, t=30, b=30))

            if (len(changed_id) == 1) & (changed_id[0] == 'radar-chart.selectedData'):
                fig['layout'].update(shapes=[])
                return dash.no_update, {'display': 'none'}, {'width': '95%', 'height': '100%'}, fig, 'Click and drag to draw a box around the area containing the points to filter. (The box should contain points, not just lines.)', False
        
#         return dash.no_update, dash.no_update, dash.no_update, dash.no_update, 'Move the sliders to modify the values of decision variables', dash.no_update

        raise PreventUpdate


@app.callback(
    Output({
        "type": "ds-sliders",
        "index": ALL
    }, "value"),
    Output('decision-values-store', 'data', allow_duplicate=True),
    Input('graph1', 'clickData'),
    Input('selected-obj-pts-store', 'data'),
    Input('graph1', 'selectedData'), 
    [
      State('stored-df', 'data'),
        State('cluster-dropdown', 'value'),
      State({
          "type": "ds-sliders",
          "index": ALL
      }, "id"),
#       State('decision-variables-store', 'data'),
    #   State('test-dropdown', 'value')
    ],
    prevent_initial_call=True)

def slider_output(click_data, obj_pts_store, selected_data, my_data, selected_cluster, slider_ids):
#     print('slider output callback')
    # if test == 'RealTimeData':
    #     min_val, max_val = 8, 20
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered]

    if my_data:
        df = pd.DataFrame(my_data)
        objective_vars = [col for col in df.columns if col.startswith(('f','T','P'))]
        decision_vars = [col for col in df.columns if col.startswith(('x','B'))]

        if 'graph1.clickData' in changed_id:
#             if 'points' in obj_pts_store and len(obj_pts_store['points']) > 0:
            if 'points' in click_data and len(click_data['points']) > 0: 
                if len(objective_vars) < 3:
                    trace_indices = [obj['pointNumber'] for obj in click_data["points"]]
                else:
                    trace_indices = [obj['curveNumber'] for obj in click_data["points"]]
                subset = df.loc[trace_indices, decision_vars].astype(float)

                if len(decision_vars) >= 5:
                    return [], subset.values.tolist()
                else:
                    slider_values = []
                    for slider_id in slider_ids:
                        if len(slider_id['index'].split('-')) < 3:
                            var = slider_id['index'].split('-')[-1]
                        else:
                            var = '-'.join(slider_id['index'].split('-')[1:])

                        if var in subset:
                            min_val = subset[var].min()
                            max_val = subset[var].max()
                        slider_values.append([min_val, max_val])
                    return slider_values, []
                
        if 'selected-obj-pts-store.data' in changed_id:
            if selected_cluster:
                if 'points' in obj_pts_store:
                    trace_indices = [obj['curveNumber'] for obj in obj_pts_store['points']]
                    subset = df.loc[trace_indices, decision_vars].astype(float)
                    if len(decision_vars) >= 5:    
                        return [], subset.values.tolist()
                    else:
                        slider_values = []
                        for col in subset.columns:
                            min_val = subset[col].min()
                            max_val = subset[col].max()
                            slider_values.append([min_val, max_val])
                        return slider_values, []
                    raise PreventUpdate
                raise PreventUpdate
                
        if 'graph1.selectedData' in changed_id:
#             print('obj', obj_pts_store)
#             print('print value', selected_data)
            if selected_data is None:
                raise PreventUpdate
                
            if 'points' in selected_data and len(selected_data['points']) > 0:
                if len(objective_vars) > 0:
                    if len(decision_vars) >= 5:
                        if len(objective_vars) < 3:
                            trace_indices = [obj['pointNumber'] for obj in selected_data["points"]]
                            subset = df.loc[trace_indices, decision_vars].astype(float)
                        else:
                            trace_indices = [obj['curveNumber'] for obj in selected_data["points"]]
                            subset = df.loc[trace_indices, decision_vars].astype(float)
                        return [], subset.values.tolist()
                    
                    # num_decision_vars < 5
                    else:
                        if len(objective_vars) < 3:
                            trace_indices = [
                                obj['pointNumber']
                                for obj in selected_data['points']
                            ]
                            subset = df.loc[trace_indices, decision_vars].astype(float)
                            print('print values < 3', subset.columns)
                        else:
                            trace_indices = [
                                obj['curveNumber']
                                for obj in selected_data['points']
                            ]
                            
#                             print('check size', len(trace_indices))
                            subset = df.loc[trace_indices, decision_vars].astype(float)
#                             print('subset', subset.shape)
                        slider_values = []
                        
                        for col in subset.columns:
                            min_val = subset[col].min()
                            max_val = subset[col].max()
#                             print("Min:",min_val,"Max:", max_val)
                            slider_values.append([min_val, max_val])
#                         print(slider_values)
                        return slider_values, []
            
    raise PreventUpdate

## COMMENT OUT PARETO FRONT CALLBACK
# @app.callback(
#     Output('graph1', "figure"),
#     Output('no-data-alert', 'is_open'),
    
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
#         Input('generated-dtlz-button', 'n_clicks'),
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
#     print('pareto', changed_id, change_status)
    
#     slider_values = dec_values_store
# #     if dims['dec'] >= 5:   
# #         slider_values = dec_values_store
        
#     if slider_values != stored_slider_values:
#         stored_slider_values = slider_values
# #         if not slider_values or all(slider == 0 for slider in slider_values):
# #             return fig
#         if data is None:
#             return curr_fig, dash.no_update
#     df = pd.DataFrame.from_dict(data)
#     fig = gen_graph(pd.DataFrame.from_dict(data))
    
#     # if len(fig.data) > 1:
#     #     fig.data = [fig.data[0]]
#     # Adding new scatter trace for the newly selected point:
#     if change_status is True:
# #         print('changed_id', changed_id)
# #         print('slider_values', slider_values)
#         if (changed_id[0] == 'graph1.selectedData') & (len(changed_id) > 1):
#             current = curr_fig.copy()
#             if dims['obj'] < 4:
#                 current['data'] = [x for x in curr_fig['data'] if 'symbol' not in x['marker']]
#                 return current, dash.no_update
#             else:
#                 new_data = []
#                 for x in curr_fig['data']:
#                     if 'marker' not in x:
#                         new_data.append(x)
#                 current['data'] = new_data
#                 return current, dash.no_update
# #             raise PreventUpdate

#         # WHEN THERE IS NO DATA
#         if not slider_values or all(slider == 0 for slider in slider_values):
#             return dash.no_update, True
        
#         # click_data = None
#         n_var = dims['dec']
#         n_obj = dims['obj']
        

#         DTLZ2 = get_problem("dtlz2", n_var=n_var, n_obj=n_obj)
#         dff = DTLZ2.evaluate(np.array([0 if x is None else x for x in slider_values]))
#         print('array for dff', len(np.array([0 if x is None else x for x in slider_values])))
#         print('dff', dff, len(dff))
# #         if len(dff) == 0:
# #             return dash.no_update, True
        
#         df = pd.DataFrame(data)
#         num_objectives = len([col for col in df.columns if col.startswith('f')])

#         if num_objectives == 2:
#             if isinstance(fig.data[0], go.Scatter):
#                 for el in dff:
#                     fig.add_scatter(x=[el[0]],
#                                     y=[el[1]],
#                                     mode='markers',
#                                     marker=dict(color='red',
#                                                 size=20,
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
#                         marker=dict(color='red', size=20),
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
#         print('status is false')
#         test = curr_fig['data']
#         num_symbols = len([d for d in test if ('marker' in d.keys())])
#         if dims['obj'] != 3:
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
#                     return fig, dash.no_update
#                 else:
#                     raise PreventUpdate
#             else:
#                 if num_symbols > 0:
#                     fig.update(data=[d for d in test if ('marker' not in d.keys())])
#                     if 'generated-dtlz-button.n_clicks' in changed_id:
#                         fig['layout'].update(shapes=[])
#                     else:
#                         if 'range' in obj_pts_store:
#                             ranges = obj_pts_store['range']
#                             selection_bounds = {
#                                 "x0": ranges["x"][0],
#                                 "x1": ranges["x"][1],
#                                 "y0": ranges["y"][0],
#                                 "y1": ranges["y"][1],
#                             }
#                             fig.add_shape(
#                                 dict(
#                                     {"type": "rect", "line": {"width": 1.5, "dash": "dot", "color": "black"}},
#                                     **selection_bounds
#                                 )
#                             )
#                 else:
#                     raise PreventUpdate

        
#         # raise PreventUpdate

#         # fig = gen_graph(pd.DataFrame.from_dict(data))

#         # REMOVE CLICK
#         else:
#             if click_data:
#                 if isinstance(fig.data[0], go.Scatter3d):
#                     if 'points' in obj_pts_store:
#                         print('check points', obj_pts_store)
#                         for pt in obj_pts_store['points']:
#                             f1_point = pt['x']
#                             f2_point = pt['y']
#                             f3_point = pt['z']

#                             fig.add_scatter3d(
#                                 x=[f1_point],
#                                 y=[f2_point],
#                                 z=[f3_point],
#                                 mode='markers',
#                                 marker=dict(color='#20b2aa', size=20),
#                                 text=f'f1: {float(f1_point): .2f}<br>f2: {float(f2_point): .2f}<br>f3: {float(f3_point): .2f}',
#                                 hoverlabel=dict(font_size=28)
#                             )
#                             fig.update_traces(hovertemplate='f1: %{x}<br>f2: %{y}<br>f3: %{z}<extra></extra>')
                    
#     fig.update_layout(showlegend=False)
#     return fig, dash.no_update


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