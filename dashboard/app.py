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
        
divFlex = {'display': 'flex', 'padding': "0.2rem", 'width': '38%'}
labelFlex = {
    'flexShrink': 0,
    'fontFamily': "Helvetica",
}

def generate_data_dtlz4(n_var, n_obj):
    problem = get_problem('dtlz4', n_var=n_var, n_obj=n_obj)
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
    print("Generated Data: ")
    print(df.head())
    return df

app.layout = html.Div([
    dcc.Store(id="slider-values-store", data={}),
    dcc.Store(id="slider-change-status", data={}),
    dcc.Store(id="df-dimensions", data={}),
    dcc.Store(id='decision-variables-store', data={}),
    dcc.Store(id="decision-values-store", data=[]),
    dcc.Store(id='selected-radar-pts-store', data=[]),
    dcc.Store(id='temp-summary-min-max', data=[]),
    interface_layout,
    html.Div(id="radar-sliders", style={'display': 'none'})
])

@app.callback(Output("data-generated", "data"), [
    Input("generated-dtlz4-button", "n_clicks")
], [State("num-decision-vars", "value"),
    State("num-objective-vars", "value"),
    ])
def generate_data_dtlz4_callback(n_clicks, n_var, n_obj):
    if n_var is None or n_obj is None:
        raise dash.exceptions.PreventUpdate("Please enter")
    if n_clicks is None:
        raise PreventUpdate
    
    df_generated = generate_data_dtlz4(n_var=n_var, n_obj=n_obj)
    filename = "data_generated.json"
    print("Generated JSON: ",df_generated.to_json(orient='records'))
    return df_generated.to_json(orient='records')

@app.callback(
    Output("summary-table", 'style'), 
    Output("summary-table", 'children'),
    Output('df-dimensions', 'data'),
    Output('decision-variables-store', 'data'),
    Output('decision-values-store', 'data'),
    [Input('upload-data', 'contents'),
     Input('upload-data', 'filename'),
     Input("data-generated", "data")])

def update_summary(contents, filename, generated_data):
    if generated_data:
        generated_data_io = io.StringIO(generated_data)
        df = pd.read_json(generated_data_io, orient='records')
    elif contents is None:
        return {'display': 'none'}, [], {}, [], dash.no_update
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
        'width': '82%'
    }, summary_table, {'obj': len(objective_functions), 'dec': len(decision_variables)}, decision_variables, [[0]]*len(decision_variables)


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

def update_output(contents, filename, tab, slider_values, click_data, selected_data, dimensions, decision_vars, decision_values, generated_data, selection_store):
#     print('update output callback')
    
    if len(dimensions) == 0:
        raise PreventUpdate

    
    if generated_data:
        df, decision_variables, objective_functions = parse_data(generated_data)
      
    elif contents is not None:
        contents = contents[0]
        filename = filename[0]
        df, decision_variables, objective_functions = parse_data(
            contents, filename)
    else:
        df = pd.DataFrame()
    
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
    
    if df is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
#     if len(changed_id) == len(decision_variables) + 1:
#         return dash.no_update, dash.no_update, dash.no_update, False
    if 'slider' in changed_id[0]:
        return dash.no_update, dash.no_update, dash.no_update, True, dash.no_update
    elif ('upload-data' in changed_id[0]) | ('data-generated.data' in changed_id):
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

        if dimensions['dec'] >= 5:
            rad_sliders = []
            default_r = [0]*len(decision_variables.keys())
            default_th = list(decision_variables.keys())

            for x in range(len(default_r)):
                rad_sliders.append(
                    html.Div([
                        html.P(f"x{x+1}", style={'fontSize': '18px'}),
                        dcc.Slider(
                            id={'type': 'dec-sliders', 'index': f'rad-slider-{x}'}, 
                            min=0, max=1, 
                            step=0.01,
                            marks=new_markers,
                            tooltip={
                                "placement": "bottom",
                                "always_visible": True
                            },
                            value=default_r[x], 
                            className='slider-5'
                        )
                    ], style={'display': 'flex', 'alignItems': 'center', 'width': '100%', 'padding': '2%'})
                )

            rad_fig = go.Figure(data=go.Scatterpolar(r=default_r, theta=default_th, line_color='red'))
            rad_fig.update_layout(dragmode='select', margin=dict(l=20, r=20, t=20, b=20))

            return fig, df.to_dict('records'), html.Div([
                html.H6(id='help'),
                dcc.Graph(id='radar-chart', figure=rad_fig, style={'width': '95%', 'height': '100%'}),
                html.Div(id='radar-sliders', style={'display': 'none'}),
            ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'space-between'}), False, dash.no_update

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
                    merged = {}
                    new_th = decision_vars.copy()
                    new_th.append(decision_vars[0])
                    
                    for i, var in enumerate(decision_vars):
                        values = [solution[i] for solution in decision_values if len(solution) == len(decision_vars)]

                        if len(values) > 0:
                            merged[var] = {'min': min(values), 'max': max(values)}

                    if len(merged) > 0:
                        # print('minimum', [merged[x]['min'] for x in new_th])
                        rad_fig.add_trace(go.Scatterpolar(r=[merged[x]['min'] for x in new_th] , theta=new_th, fill='toself', mode='lines', name='Min solutions'))
                        rad_fig.add_trace(go.Scatterpolar(r=[merged[x]['max'] for x in new_th], theta=new_th, fill='toself', mode='lines', name='Max solutions'))

                    for solution in decision_values:
                        new_r = solution
                        new_r.append(solution[0])
                        
                        rad_fig.add_trace(go.Scatterpolar(r=new_r, theta=new_th))



                rad_fig.update_layout(showlegend=False, dragmode='select', margin=dict(l=20, r=20, t=20, b=20))
                        
                return dash.no_update, dash.no_update, html.Div([
                        html.H6(id='help', children='Click and drag to draw a box around the area containing the points to filter.'),
                        html.Div([
                            dcc.Graph(id='radar-chart', figure=rad_fig, style={'width': '95%', 'height': '95%'}),
                            html.Div(id='radar-sliders', style={'display': 'none'})
                        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'width': '100%', 'height': '100%'})
                    ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'space-between'}), False, merged
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

                
                
    elif click_data:
        if selection_store is None:
            if dimensions['dec'] >= 5:
                rad_fig = go.Figure(data=go.Scatterpolar(r=[], theta=[]))
                sliders = []
                r = decision_values

                if len(decision_values) > 0:
                    th = decision_vars
                    th.append(th[0])

                    r = decision_values
                    r.append(r[0])
                    rad_fig = go.Figure(data=go.Scatterpolar(r=r, theta=th, line_color='red'))

                    for x in range(len(r)-1):
                        sliders.append(
                            html.Div([
                                html.P(f"x{x+1}", style={'fontSize': '18px'}),
                                dcc.Slider(
                                    id={'type': 'dec-sliders', 'index': f'rad-slider-{x}'}, 
                                    min=0, max=1, step=0.01, 
                                    marks=new_markers,
                                    tooltip={
                                        "placement": "bottom",
                                        "always_visible": True
                                    },
                                    value=r[x],
                                    className='slider-5'
                                )
                            ], style={'display': 'flex', 'alignItems': 'center', 'width': '100%', 'padding': '2%'})
                        )

                    rad_fig.update_layout(dragmode='select', margin=dict(l=20, r=20, t=20, b=20))

                return dash.no_update, dash.no_update, html.Div([
                        html.H6(id='help', children='Click and drag to draw a box around the area containing the points to filter.'),
                        html.Div([
                            dcc.Graph(id='radar-chart', figure=rad_fig, style={'width': '95%', 'height': '95%'}),
                            html.Div(id='radar-sliders', style={'display': 'none'})
                        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'width': '100%', 'height': '100%'})
                    ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'space-between'}), False, dash.no_update

        return dash.no_update, dash.no_update, dash.no_update, False, dash.no_update
    
    return dash.no_update, dash.no_update, dash.no_update, False, dash.no_update

def update_bounding_box(slider_values, radar_sliders_style, fig, radar_sliders, dec_values, radar_pts):
#     print('update bounding box')
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
    if radar_pts is None:
        return dash.no_update, False
    if 'shapes' in fig['layout']:
        # filtered_ids = [el['props']['children'][0]['props']['children'] for el in radar_sliders]
        # filtered_sliders = slider_values
        # chartAxisRange = fig['layout']['polar']['radialaxis']['range']
        if len(changed_id) == 1:
            return dash.no_update, True
        return dash.no_update, False
    raise PreventUpdate

@app.callback(
    Output('selected-radar-pts-store', 'data'),
    Input('radar-chart', 'selectedData'),
    Input({
        "type": "dec-sliders",
        "index": ALL
    }, "value"),
    Input('graph1', 'clickData'),
    Input('graph1', 'selectedData'),
    State('decision-variables-store', 'data'),
    prevent_initial_call=True
)

def save_selection(radar_selected, dec_sliders, click_data, selected_data, dec_vars):
    if len(dec_vars) >= 5:
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
        if 'rad-slider-' in changed_id[0]:
            raise PreventUpdate
        if 'clickData' in changed_id[0]:
            return None
        return radar_selected
#         raise PreventUpdate
    raise PreventUpdate

@app.callback(
    Output('radar-sliders', 'children'),
    Output('radar-sliders', 'style'),
    Output('radar-chart', 'style'),
    Output('radar-chart', 'figure', allow_duplicate=True),
    Output('help', 'children'),
    Output('slider-change-status', 'data', allow_duplicate=True),
    Input('radar-chart', 'selectedData'),
    Input('radar-chart', 'figure'),
    State('temp-summary-min-max', 'data'),
    State('decision-values-store', 'data'),
    State('decision-variables-store', 'data'),
    State('graph1', 'figure'),
    prevent_initial_call=True
)

def filter_sliders(selected_radar_values, fig, summary, stored_sliders, decision_vars, pc_fig):
    # print('filter sliders callback')
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
    if selected_radar_values:
        # print('printing...', selected_radar_values['points'])
        filtered_vars = list(set([obj['theta'] for obj in selected_radar_values['points']]))
        filtered_indices = [decision_vars.index(x) for x in filtered_vars]

        # Get filtered ranges by theta
        combined = {}
        for obj in selected_radar_values['points']:
            if obj['theta'] in combined:
                combined[obj['theta']]['values'].append(obj['r'])
            else:
                combined[obj['theta']] = {'values': [obj['r']]}
                
        new_sliders = []        
        for v in filtered_vars:
            idx = decision_vars.index(v)
            new_sliders.append(
                html.Div([
                    html.P(f"{v}", style={'fontSize': '18px'}),
                    dcc.RangeSlider(
                        id={'type': 'dec-sliders', 'index': f'rad-slider-{decision_vars.index(v)}'},
                        min=0, max=1, step=0.01,
                        marks=new_markers,
                        tooltip={
                            "placement": "bottom",
                            "always_visible": True
                        },
                        value=[min([values[idx] for values in stored_sliders]), max([values[idx] for values in stored_sliders])],
                        className='slider-5'
                    )
                ], style={'display': 'flex', 'alignItems': 'center', 'width': '100%', 'padding': '2%'})
            )
            
        new_th = decision_vars
        new_th.append(decision_vars[0])
 
        chartAxisRange = fig['layout']['polar']['radialaxis']['range']
        boundingBox = selected_radar_values['range']
        
        converted_x = []
        converted_y = []
        for x in boundingBox['x']:
            # convert scale to use chart axis range
            tmp_x = x+chartAxisRange[1]
            # calculate percentage on scale
            perc_x = tmp_x/(chartAxisRange[1]*2)
            # re-calculate on a different scale
            converted_x.append(perc_x)
            
            
        for y in boundingBox['y']:
            # convert scale to use chart axis range
            tmp_y = y+chartAxisRange[1]
            # calculate percentage on scale
            perc_y = tmp_y/(chartAxisRange[1]*2)
            # re-calculate on a different scale
            converted_y.append(perc_y*(0.85-0.15)+0.15)   
        
        rad_fig = go.Figure(fig)
        # for solution in stored_sliders:
        #     r = solution
        #     r.append(solution[0])
        #     rad_fig.add_trace(go.Scatterpolar(r=r, theta=new_th))
        
        rad_fig.add_shape(
            type="rect",
            x0=converted_x[0], x1=converted_x[1], 
            y0=converted_y[0], y1=converted_y[1],
            xref='x domain', yref='y domain',  
            xsizemode='scaled', ysizemode='scaled',
            line=dict(color="black", dash='dot', width=1),
        )

        rad_fig.update_layout(showlegend=False, dragmode='select', margin=dict(l=0, r=0, t=0, b=0))
        
        return new_sliders, {'display': 'block', 'width': '45%'}, {'width': '50%', 'height': '100%'}, rad_fig, 'Move the sliders to modify the values of filtered variables and double-click on an empty area in the chart to deselect.', False
    else:
        if len(decision_vars) >= 5:
            th = decision_vars
            th.append(decision_vars[0])

            rad_fig = go.Figure()
            if len(summary) > 0:
                rad_fig.add_trace(go.Scatterpolar(r=[summary[x]['min'] for x in th] , theta=th, fill='toself', mode='lines', name='Minimum'))
                rad_fig.add_trace(go.Scatterpolar(r=[summary[x]['max'] for x in th], theta=th, fill='toself', mode='lines', name='Maximum'))
            for solution in stored_sliders:
                r = solution
                r.append(solution[0])
                rad_fig.add_trace(go.Scatterpolar(r=r, theta=th))



            rad_fig.update_layout(showlegend=False, dragmode='select', margin=dict(l=20, r=20, t=20, b=20))

            if (len(changed_id) == 1) & (changed_id[0] == 'radar-chart.selectedData'):
                return dash.no_update, {'display': 'none'}, {'width': '95%', 'height': '100%'}, rad_fig, 'Click and drag to draw a box around the area containing the points to filter.', False
            return dash.no_update, {'display': 'none'}, {'width': '95%', 'height': '100%'}, dash.no_update, 'Click and drag to draw a box around the area containing the points to filter.', dash.no_update
        raise PreventUpdate

@app.callback(
    Output({
        "type": "ds-sliders",
        "index": ALL
    }, "value"),
    Output('decision-values-store', 'data', allow_duplicate=True),
    Input('graph1', 'clickData'), 
    Input('graph1', 'selectedData'),
    [
        State('stored-df', 'data'),
        State({
            "type": "ds-sliders",
            "index": ALL
        }, "id")
    ],
    prevent_initial_call=True
)
def slider_output(click_data, selected_data, my_data, slider_ids):
    if selected_data and my_data:
        df = pd.DataFrame(my_data)
        if 'points' in selected_data and len(selected_data['points']) > 0:
            num_objectives = len([col for col in df.columns if col.startswith('f')])
            num_decision_vars = len(df.columns) - num_objectives
            
            if num_objectives > 0:
                # Extracting x, y, z coordinates if applicable
                x_key = 'x'
                y_key = 'y'
                z_key = 'z' if num_objectives >= 3 else None

                if num_objectives <= 3:
                    f1_point = click_data['points'][0][x_key]
                    f2_point = click_data['points'][0][y_key]
                    f3_point = click_data['points'][0][z_key] if z_key else None

                    dff = df[(df["f1"] == f1_point) & (df["f2"] == f2_point)]
                    if f3_point:
                        dff = dff[dff["f3"] == f3_point]

                    if not dff.empty:
                        if len(slider_ids) > 0:
                            decision_variables = [
                                id['index'].split('-')[1] for id in slider_ids
                            ]
                            if pd.Series(decision_variables).isin(dff.columns).all():
                                values = [float(x) for x in list(dff[decision_variables].iloc[0])]
                                return values, values
                        # if len(slider_values) == len(slider_ids):
                        #     return slider_values
                        else:
                            decision_variables = [key for key in list(my_data[0].keys()) if 'x' in key]
                            if pd.Series(decision_variables).isin(dff.columns).all():
                                return [], list(dff[decision_variables].values[0])
                else:
#                     print(selected_data['points'])
                    trace_indices = [obj['curveNumber'] for obj in selected_data["points"]]
#                     print(trace_indices)

                    subset = df.iloc[trace_indices, :num_decision_vars].astype(float)
                    if num_decision_vars >= 5:
                        return [], subset.values.tolist()
                    return subset.values.tolist(), []      
    raise PreventUpdate


@app.callback(
    Output('graph1', "figure"),
    [
        Input({
            "type": "ds-sliders",
            "index": ALL
        }, "value"),
        Input({
            "type": "dec-sliders",
            "index": ALL
        }, "value"),
        Input('decision-values-store', 'data'),
        Input('graph1', 'clickData'),
        Input('graph1', 'selectedData'),
        Input('slider-change-status', 'data'),
        Input('graph1', "figure"),
        Input('radar-sliders', 'style'),
    ],
    [
        State('stored-df', 'data'),
        State('slider-values-store', 'data'),
        State('df-dimensions', 'data'),
        State('selected-radar-pts-store', 'data'),
    ],
    prevent_initial_call=True)

def pareto_front(ds_slider_values, dec_slider_values, dec_values_store, click_data, selected_data, change_status, curr_fig, rad_sliders_style, data,
                 stored_slider_values, dims, selection_store):
    
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
    slider_values = ds_slider_values
    if dims['dec'] >= 5:
        slider_values = dec_values_store
        
    if slider_values != stored_slider_values:
        stored_slider_values = slider_values
#         if not slider_values or all(slider == 0 for slider in slider_values):
#             return fig
        if data is None:
            return curr_fig
    df= pd.DataFrame.from_dict(data)
    fig = gen_graph(pd.DataFrame.from_dict(data))

    # if len(fig.data) > 1:
    #     fig.data = [fig.data[0]]
    # Adding new scatter trace for the newly selected point:
    if change_status is True:
        if not slider_values or all(slider == 0 for slider in slider_values):
            return fig
        # click_data = None
        n_var = dims['dec']
        n_obj = dims['obj']

        DTLZ2 = get_problem("dtlz2", n_var=n_var, n_obj=n_obj)
        dff = DTLZ2.evaluate(np.array([0 if x is None else x for x in slider_values ]))
        df = pd.DataFrame(data)
        num_objectives = len(
            [col for col in df.columns if col.startswith('f')])
        if num_objectives == 2:
            if isinstance(fig.data[0], go.Scatter):
                fig.add_scatter(x=[dff[0]],
                                y=[dff[1]],
                                mode='markers',
                                marker=dict(color='red',
                                            size=30,
                                            symbol='star'),
                                hoverinfo='text',
                                text=f'f1: {dff[0]: .2f}<br>f2: {dff[1]: .2f}',
                                hoverlabel=dict(font_size=22))
        elif num_objectives == 3:
            if isinstance(fig.data[0], go.Scatter3d):
                fig.add_scatter3d(
                    x=[dff[0]],
                    y=[dff[1]],
                    z=[dff[2]],
                    mode='markers',
                    marker=dict(color='red', size=30),
                    hoverinfo='text',
                    text=
                    f'f1: {dff[0]: .2f}<br>f2: {dff[1]: .2f}<br>f3: {dff[2]: .2f}',
                    hoverlabel=dict(font_size=22))
        elif num_objectives > 3:
            if isinstance(fig.data[0], go.Scatter):
                x_labels = [f'f{i+1}' for i in range(len(dff))]
#                 print('x_labels', x_labels)

                for el in dff:
                    fig.add_scatter(
                        x=x_labels,
                        y=el,
                        mode='lines+markers',
                        line=dict(color='red', width=5),
                        marker=dict(color='red', size=30, symbol='star'),
                        hoverinfo='text',
                        text='<br>'.join([
                            f'{label}: {value: .2f}'
                            for label, value in zip(x_labels, el)
                        ]),
                        # text=f'f1: {dff[0]: .2f}<br>f2: {dff[1]: .2f}<br>f3: {dff[2]: .2f}<br>f4: {dff[3]: .2f}',
                        hoverlabel=dict(font_size=22))
    else:
#         print('check', changed_id)
#         if selected_data:
        # if ('slider-change-status.data' in changed_id) & (selection_store is None) & len(changed_id) < 3:
        #     return fig

            
        # raise PreventUpdate

        # fig = gen_graph(pd.DataFrame.from_dict(data))
        if click_data:
            if isinstance(fig.data[0], go.Scatter):
                f1_point = click_data['points'][0]['x']
                f2_point = click_data['points'][0]['y']
                selected_trace_index = click_data['points'][0]['curveNumber']
                selected_trace = fig.data[selected_trace_index]

                # if selected_trace:
                if isinstance(selected_trace,
                              go.Scatter) and selected_trace.mode == 'lines':
                    selected_trace.line.color = 'black'
                    selected_trace.line.width = 10
                    selected_values = df.iloc[selected_trace_index].values
                    x_labels = [f'f{i+1}' for i in range(len(selected_values))]
                    selected_trace.text = '<br>'.join([
                        f'{label}: {value: .2f}'
                        for label, value in zip(x_labels, selected_values)
                    ])
                    selected_trace.hoverinfo = 'text'
                    for i, trace in enumerate(fig.data):
                        if isinstance(
                                trace, go.Scatter
                        ) and trace.mode == 'lines' and i != selected_trace_index:
                            trace.line.color = 'rgb(203, 195, 227)'
                            trace.opacity = 0.2

                highlighted_trace = go.Scatter(x=[f1_point],
                                y=[f2_point],
                                mode='lines+markers',
                                line=dict(color='black', width=30),
                                marker=dict(color='black', size=30),
                                hoverlabel=dict(font_size=28),
                                hovertemplate=None,
                                hoverinfo='text',
                                text='<br>'.join([
                        f'{label}: {value: .2f}'
                        for label, value in zip([f1_point], [f2_point])
                    ]),
                                name="")
                fig.update_traces(visible= True)
                highlighted_index = None
                for i, trace in enumerate(fig.data):
                    if isinstance(trace, go.Scatter) and trace.mode == 'lines+markers':
                        highlighted_index = i
                        break
                        
                if highlighted_index is not None:
                    fig.data.pop(highlighted_index)
                
                fig.add_trace(highlighted_trace)
                    
                if selected_data:
                    for point in selected_data['points']:
                        selected_trace_index = point['curveNumber']
                        if selected_trace_index != highlighted_index:
                            selected_trace = fig.data[selected_trace_index]
                            selected_trace.opacity = 1.0
                            selected_trace.line.color = 'black'
            elif isinstance(fig.data[0], go.Scatter3d):
                f1_point = click_data['points'][0]['x']
                f2_point = click_data['points'][0]['y']
                f3_point = click_data['points'][0]['z']
                fig.add_scatter3d(x=[f1_point],
                                  y=[f2_point],
                                  z=[f3_point],
                                  mode='markers',
                                  marker=dict(color=f"rgb(32,178,170)", size=30),
                                  text=
                    f'f1: {f1_point: .2f}<br>f2: {f2_point: .2f}<br>f3: {f3_point: .2f}',
                    hoverlabel=dict(font_size=28))
                fig.update_traces(
                    hovertemplate=
                    'f1: %{x}<br>f2: %{y}<br>f3: %{z}<extra></extra>')
            # elif isinstance(fig.data[0], go.Parcoords):
            #     coords = [
            #         click_data['points'][0]['dimension_values'][i]
            #         for i in range(len(data[0]))
            #     ]
            #     dimensions = [{
            #         "label": f"Objective {i+1}",
            #         "values": [coords[i]]
            #     } for i in range(len(coords))]
            #     if len(fig.data) == 1:
            #         fig.add_trace(
            #             go.Parcoords(line=dict(color='LightSeaGreen', size=30),
            #                          dimensions=dimensions))
            #     else:
            #         fig.data[1].dimensions = dimensions
                    
    fig.update_layout(showlegend=False)
    return fig

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=5001)
