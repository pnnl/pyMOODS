import base64
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
from dashlib.components import gen_graph
from data.parser import parse_data
from logger.custom import NumpyEncoder
from dash.exceptions import PreventUpdate

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

# app.layout = interface_layout

app.layout = html.Div([
    dcc.Store(id="slider-values-store", data={}),
    dcc.Store(id="slider-change-status", data={}),
    dcc.Store(id="df-dimensions", data={}),
    dcc.Store(id='decision-variables-store', data={}),
    dcc.Store(id="decision-values-store", data=[]),
    dcc.Store(id='selected-radar-pts-store', data=[]),
    dcc.Store(id='selection-bbox', data={}),
    interface_layout
])




@app.callback(
    Output("summary-table", 'style'), 
    Output("summary-table", 'children'),
    Output('df-dimensions', 'data'),
    Output('decision-variables-store', 'data'),
    Output('decision-values-store', 'data'),
    [Input('upload-data', 'contents'),
     Input('upload-data', 'filename')])

def update_summary(contents, filename):
#     print('update summary callback')
    if contents is None:
        return {'display': 'none'}, [], {}, [], dash.no_update

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
    }, summary_table, {'obj': len(objective_functions), 'dec': len(decision_variables)}, decision_variables, [0]*len(decision_variables)


@app.callback(Output("graph1", "figure", allow_duplicate=True),
              Output("stored-df", "data"),
              Output("sliders", "children"),
              Output("slider-change-status", "data"),
              Input("upload-data", "contents"),
              Input("upload-data", "filename"),
              Input('tabs-example-graph', 'value'),
              Input({
                  "type": "ds-sliders",
                  "index": ALL
              }, "value"),
              Input("graph1", "clickData"),
              Input('df-dimensions', 'data'),
              Input('decision-variables-store', 'data'),
              Input('decision-values-store', 'data'),
              State('selected-radar-pts-store', 'data'),
              prevent_initial_call=True)

def update_output(contents, filename, tab, slider_values, click_data, dimensions, decision_vars, decision_values, selection_store):
#     print('update output callback')
    if len(dimensions) == 0:
        raise PreventUpdate
        
    print(dimensions['dec'])


    changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
    
    if contents is not None:
        contents = contents[0]
        filename = filename[0]
        df, decision_variables, objective_functions = parse_data(
            contents, filename)
    
    if df is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
#     if len(changed_id) == len(decision_variables) + 1:
#         return dash.no_update, dash.no_update, dash.no_update, False
    if 'slider' in changed_id[0]:
        return dash.no_update, dash.no_update, dash.no_update, True
    elif 'upload-data' in changed_id[0]:
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
                dcc.Graph(id='radar-chart', figure=rad_fig, style={'width': '95%', 'height': '100%'}),
                html.Div(id='radar-sliders', style={'display': 'none'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}), False

        sliders = [
            html.Div(
                [
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

        return fig, df.to_dict('records'), sliders, False
    
    elif click_data:
#         print('graph1 click data', selection_store)
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
                        dcc.Graph(id='radar-chart', figure=rad_fig, style={'width': '95%', 'height': '100%'}),
                        html.Div(id='radar-sliders', style={'display': 'none'})
                    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}), False
        else:
#             r = decision_values
#             r.append(decision_values[0])
            
#             th = decision_vars
#             th.append(decision_vars[0])
# #             print('checking error')
# #             print(r, th)
            
#             rad_fig = go.Figure(data=go.Scatterpolar(r=r, theta=th, line_color='red'))
#             rad_fig.update_layout(dragmode='select', margin=dict(l=20, r=20, t=20, b=20))
            
#             return dash.no_update, dash.no_update, html.Div([
#                         dcc.Graph(id='radar-chart', figure=rad_fig, style={'width': '50%', 'height': '100%'}),
#                         html.Div(id='radar-sliders', style={'width': '45%', 'display': 'block'})
#                     ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}), False
            raise PreventUpdate
        return dash.no_update, dash.no_update, dash.no_update, False

    
    return dash.no_update, dash.no_update, dash.no_update, False

# @app.callback(
#     Output('selected-radar-pts-store', 'data'),
#     Input('radar-chart', 'selectedData'),
#     State('selected-radar-pts-store', 'data'),
# #     Input({
# #         "type": "dec-sliders",
# #         "index": ALL
# #     }, "value"),
# #     Input('decision-values-store', 'data'),
# #     prevent_initial_call=True
# )

# def save_radar_selection(selectedData, curr_selected_pts):
#     changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
#     print('ch', changed_id)
#     print('called', selectedData)
    
#     if selectedData is None:
#         print('current', curr_selected_pts)
#         raise Prevent
#     else:
#         return selectedData

# @app.callback(
# #     Output('radar-chart', 'selectedData'),
#     Output('selected-radar-pts-store', 'data'),
# #     Input('decision-values-store', 'data'),
#     Input({
#         "type": "dec-sliders",
#         "index": ALL
#     }, "value"),
#     Input('radar-chart', 'selectedData'),
# #     State('radar-chart', 'selectedData'),
#     prevent_initial_call=True
# )

# def update_selection(dec_slider_values, selectedData):
#     changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
#     print('check this', changed_id)
#     if 'rad-slider-' in changed_id[0]:
#         print('here')
#         raise PreventUpdate
#     return selectedData

@app.callback(
    Output('selected-radar-pts-store', 'data'),
    Input('radar-chart', 'selectedData'),
    Input({
        "type": "dec-sliders",
        "index": ALL
    }, "value"),
    Input('graph1', 'clickData'),
    State('decision-variables-store', 'data'),
    prevent_initial_call=True
)

def save_selection(selectedData, dec_sliders, click_data, dec_vars):
    if len(dec_vars) >= 5:
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
        print('ch', changed_id)
        if 'rad-slider-' in changed_id[0]:
            raise PreventUpdate
        if 'clickData' in changed_id[0]:
            return None
        return selectedData
    raise PreventUpdate

@app.callback(
    Output('radar-sliders', 'children'),
    Output('radar-sliders', 'style'),
    Output('radar-chart', 'style'),
    Output('radar-chart', 'figure'),
    Output('selection-bbox', 'data'),
    Input('radar-chart', 'selectedData'),
    Input('radar-chart', 'figure'),
#     Input('radar-chart', 'selectedData'),
    State('decision-values-store', 'data'),
    State('decision-variables-store', 'data'),
    
    prevent_initial_call=True
)

def filter_sliders(selected_radar_values, fig, stored_sliders, decision_vars):
    if selected_radar_values:
        filtered = list(set([d['theta'] for d in selected_radar_values['points']]))

        t = sorted([int(el.split('x')[1]) for el in filtered])
        new_sliders = []
        for i in range(len(filtered)):
            new_sliders.append(
                html.Div([
                    html.P(f"x{t[i]}", style={'fontSize': '18px'}),
                    dcc.Slider(
                        id={'type': 'dec-sliders', 'index': f'rad-slider-{t[i]}'}, 
                        min=0, max=1, step=0.1,
                        marks=new_markers,
                        tooltip={
                            "placement": "bottom",
                            "always_visible": True
                        },
                        value=stored_sliders[t[i]-1],
                        className='slider-5'
                    )
                ], style={'display': 'flex', 'alignItems': 'center', 'width': '100%', 'padding': '2%'})
            )
        
#         print('vars', decision_vars)
#         print('filtered', filtered)
        
        new_th = decision_vars
        new_th.append(decision_vars[0])
        
        new_r = stored_sliders
        new_r.append(stored_sliders[0])
        
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
        
        rad_fig = go.Figure(data=go.Scatterpolar(r=new_r, theta=new_th, line_color='red', selectedpoints=[decision_vars.index(x) for x in filtered]))
        rad_fig.add_shape(
            type="rect",
            x0=converted_x[0], x1=converted_x[1], 
            y0=converted_y[0], y1=converted_y[1],
            xref='x domain', yref='y domain',  
            xsizemode='scaled', ysizemode='scaled',
            line=dict(color="#a3a5a9", dash='dot', width=1),
        )

        rad_fig.update_layout(dragmode='select', margin=dict(l=0, r=0, t=0, b=0))
        
        return new_sliders, {'display': 'block', 'width': '45%'}, {'width': '50%', 'height': '100%'}, rad_fig, {'x': converted_x, 'y': converted_y}
    else:
        if len(decision_vars) >= 5:
            th = decision_vars
            th.append(decision_vars[0])

            r = stored_sliders
            r.append(stored_sliders[0])

            rad_fig = go.Figure(data=go.Scatterpolar(r=r, theta=th, line_color='red'))
            rad_fig.update_layout(dragmode='select', margin=dict(l=20, r=20, t=20, b=20))

            return dash.no_update, {'display': 'none'}, {'width': '95%', 'height': '100%'}, rad_fig, {}
        raise PreventUpdate

@app.callback(
    Output('decision-values-store', 'data', allow_duplicate=True),
    Input({
        "type": "dec-sliders",
        "index": ALL
    }, "value"),
    State('decision-values-store', 'data'),
    State('decision-variables-store', 'data'),
    State('radar-chart', 'selectedData'),
#     State('selected-radar-pts-store', 'data'),
    prevent_initial_call=True
)

def save_decision_values(slider_values, curr_dec_values, dec_variables, selected_points):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
#     print('changed', changed_id, selected_points)
    if len(dec_variables) >= 5:
        if len(changed_id) == 1:
            if 'rad-slider-' in changed_id[0]:
                filtered_labels = sorted(list(set([d['theta'] for d in selected_points['points']])))
                filtered_labels_indices = [dec_variables.index(label) for label in filtered_labels]

                new_r = curr_dec_values
                for i, x in enumerate(filtered_labels_indices):
                    new_r[x] = slider_values[i]
                return new_r
            raise PreventUpdate
        else:
            raise PreventUpdate
    raise preventUpdate
        
@app.callback(
    Output('radar-chart', 'figure', allow_duplicate=True),
    Input({
        'type': 'dec-sliders',
        'index': ALL,
    }, 'value'),
    State('radar-chart', 'figure'),
    prevent_initial_call=True
)    

def save_selection(dec_slider_values, fig):
    triggered_id = [p['prop_id'] for p in ctx.triggered]
    if 'rad-slider-' in triggered_id[0]:
        return fig
    raise PreventUpdate
    

@app.callback(
    Output({
        "type": "ds-sliders",
        "index": ALL
    }, "value"),
    Output('decision-values-store', 'data', allow_duplicate=True),
    Input('graph1', 'clickData'), [
        State('stored-df', 'data'),
        State({
            "type": "ds-sliders",
            "index": ALL
        }, "id")
    ],
    prevent_initial_call=True
)
def slider_output(click_data, my_data, slider_ids):
    if click_data and my_data:
        df = pd.DataFrame(my_data)
        if 'points' in click_data and len(click_data['points']) > 0:
            # Extracting coordinates based on the plot type
            num_objectives = len(
                [col for col in df.columns if col.startswith('f')])
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
                    trace_index = click_data["points"][0]["curveNumber"]
#                     print('trace_index', trace_index)
                    if 0 <= trace_index < len(df):
                        slider_values = df.iloc[
                            trace_index, :num_decision_vars].tolist()
                        if num_decision_vars >= 5:
                            return [], [float(x) for x in slider_values]
                        return [float(x) for x in slider_values], []
                    
    return [0 for _ in slider_ids], [0 for _ in slider_ids]
#     raise PreventUpdate


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
        Input('slider-change-status', 'data')
    ],
    [
        State('graph1', "figure"),
        State('stored-df', 'data'),
        State('slider-values-store', 'data'),
        State('df-dimensions', 'data')
    ],
    prevent_initial_call=True)

def pareto_front(ds_slider_values, dec_slider_values, dec_values_store, click_data, change_status, fig, data,
                 stored_slider_values, dims):
    slider_values = ds_slider_values
    if dims['dec'] >= 5:
        slider_values = dec_values_store
        
    if slider_values != stored_slider_values:
        stored_slider_values = slider_values
#         if not slider_values or all(slider == 0 for slider in slider_values):
#             return fig
        if data is None:
            return fig
    fig = gen_graph(pd.DataFrame.from_dict(data))

    # if len(fig.data) > 1:
    #     fig.data = [fig.data[0]]
    # Adding new scatter trace for the newly selected point:
    if change_status is True:
        if not slider_values or all(slider == 0 for slider in slider_values):
            print('in this if')
            return fig
        # click_data = None
        n_var = dims['dec']
        n_obj = dims['obj']

        DTLZ2 = get_problem("dtlz2", n_var=n_var, n_obj=n_obj)
        dff = DTLZ2.evaluate(np.array([0 if x is None else x for x in slider_values ]))
#         print('checking...', [0 if x is None else x for x in slider_values ], dff)
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
                fig.add_scatter(
                    x=x_labels,
                    y=dff,
                    mode='lines+markers',
                    line=dict(color='red', width=5),
                    marker=dict(color='red', size=30, symbol='star'),
                    hoverinfo='text',
                    text='<br>'.join([
                        f'{label}: {value: .2f}'
                        for label, value in zip(x_labels, dff)
                    ]),
                    # text=f'f1: {dff[0]: .2f}<br>f2: {dff[1]: .2f}<br>f3: {dff[2]: .2f}<br>f4: {dff[3]: .2f}',
                    hoverlabel=dict(font_size=22))
    else:
        # fig = gen_graph(pd.DataFrame.from_dict(data))
        if click_data:
#             print('click data')
#             print(fig.data[0])
            if isinstance(fig.data[0], go.Scatter):
                f1_point = click_data['points'][0]['x']
                f2_point = click_data['points'][0]['y']
                fig.add_scatter(x=[f1_point],
                                y=[f2_point],
                                marker=dict(color='LightSeaGreen', size=30))
                # fig.update_traces(
                #     hovertemplate='f1: %{x}<br>f2: %{y}<extra></extra>')
            elif isinstance(fig.data[0], go.Scatter3d):
                f1_point = click_data['points'][0]['x']
                f2_point = click_data['points'][0]['y']
                f3_point = click_data['points'][0]['z']
                fig.add_scatter3d(x=[f1_point],
                                  y=[f2_point],
                                  z=[f3_point],
                                  mode='markers',
                                  marker=dict(color='LightSeaGreen', size=30))
                fig.update_traces(
                    hovertemplate=
                    'f1: %{x}<br>f2: %{y}<br>f3: %{z}<extra></extra>')
            elif isinstance(fig.data[0], go.Parcoords):
                coords = [
                    click_data['points'][0]['dimension_values'][i]
                    for i in range(len(data[0]))
                ]
                dimensions = [{
                    "label": f"Objective {i+1}",
                    "values": [coords[i]]
                } for i in range(len(coords))]
                if len(fig.data) == 1:
                    fig.add_trace(
                        go.Parcoords(line=dict(color='LightSeaGreen', size=30),
                                     dimensions=dimensions))
                else:
                    fig.data[1].dimensions = dimensions
                    
    fig.update_layout(showlegend=False)
    return fig


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=5001)
