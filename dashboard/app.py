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
    interface_layout
])


@app.callback(
    Output("summary-table", 'style'), 
    Output("summary-table", 'children'),
    Output('df-dimensions', 'data'),
    Output('decision-variables-store', 'data'),
    [Input('upload-data', 'contents'),
     Input('upload-data', 'filename')])

def update_summary(contents, filename):
    if contents is None:
        return {'display': 'none'}, [], {}, []

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
    }, summary_table, {'obj': len(objective_functions), 'dec': len(decision_variables)}, decision_variables


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
              Input('decision-values-store', 'data'),
              prevent_initial_call=True)

def update_output(contents, filename, tab, slider_values, click_data, dimensions, decision_store):
#     print('update_output...')
    if len(dimensions) == 0:
        raise PreventUpdate

    changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
    print(changed_id)
    
    if 'decision-values-store.data' in changed_id:
        print(decision_store)

    if contents is not None:
        contents = contents[0]
        filename = filename[0]
        df, decision_variables, objective_functions = parse_data(
            contents, filename)
    
    if df is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
#     print(len(decision_variables))
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
#             print(default_r, default_th)

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
#                 rad_sliders.append(html.P(f"Decision Variable - {x+1}"))
#                 rad_sliders.append(dcc.Slider(
#                     id={'type': 'dec-sliders', 'index': f'rad-slider-{x}'}, 
#                     min=0, max=1, 
#                     step=0.01,
#                     marks=new_markers,
#                     tooltip={
#                         "placement": "bottom",
#                         "always_visible": True
#                     },
#                     value=default_r[x], 
#                     className='slider-marker'
#                 ))

            rad_fig = go.Figure(data=go.Scatterpolar(r=default_r, theta=default_th, line_color='red'))
            rad_fig.update_layout(dragmode='select', margin=dict(l=20, r=20, t=20, b=20))

            return fig, df.to_dict('records'), html.Div([
                dcc.Graph(id='radar-chart', figure=rad_fig, style={'width': '35%', 'height': '100%'}),
                html.Div(id='radar-sliders', children=rad_sliders, style={'width': '60%', 'fontSize': '16px'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}), False

        sliders = [
            html.Div(
                [
                    html.Div(col, style=labelFlex, className="slider-label"),
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
        if dimensions['dec'] >= 5:
#             print('in here', decision_store)
            rad_fig = go.Figure(data=go.Scatterpolar(r=[], theta=[]))
            sliders = []
            r = decision_store

            if len(decision_store) > 0:
                th = [f'x{i+1}' for i in range(len(decision_store))]
                th.append(th[0])

                r = decision_store
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
#                     sliders.append(html.P(f"Decision Variable - {x+1}"))
#                     sliders.append(dcc.Slider(
#                         id={'type': 'dec-sliders', 'index': f'rad-slider-{x}'}, 
#                         min=0, max=1, step=0.01, 
#                         marks=new_markers,
#                         tooltip={
#                             "placement": "bottom",
#                             "always_visible": True
#                         },
#                         value=r[x],
#                         className='slider-marker'
#                     ))
                rad_fig.update_layout(dragmode='select', margin=dict(l=20, r=20, t=20, b=20))

            return dash.no_update, dash.no_update, html.Div([
                    dcc.Graph(id='radar-chart', figure=rad_fig, style={'width': '40%', 'height': '100%'}),
                    html.Div(id='radar-sliders', children=sliders, style={'width': '55%', 'fontSize': '14px'}),
#                         dcc.Store(id='sliders-store', data=r)
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}), False
        return dash.no_update, dash.no_update, dash.no_update, False
    return dash.no_update, dash.no_update, dash.no_update, False

@app.callback(
    Output('radar-sliders', 'children'),
    Input('radar-chart', 'selectedData'),
    State('decision-values-store', 'data'),
    prevent_initial_call=True
)

def filter_sliders(radar_values, stored_sliders):
    if radar_values is None:
        tmp_sliders = []
        for i in range(len(stored_sliders)):
            tmp_sliders.append(
                html.Div([
                    html.P(f"Decision Variable - {i+1}", style={'fontSize': '18px'}),
                    dcc.Slider(
                        id={'type': 'dec-sliders', 'index': f'rad-slider-{stored_sliders[i]}'}, 
                        min=0, max=1, step=0.1, 
                        marks=new_markers,
                        tooltip={
                            "placement": "bottom",
                            "always_visible": True
                        },
                        value=stored_sliders[i],
                        className='slider-5'
                    )
                ], style={'display': 'flex', 'alignItems': 'center', 'width': '100%', 'padding': '2%'})
            )
#             tmp_sliders.append(html.P(f"Decision Variable - {i+1}"))
#             tmp_sliders.append(dcc.Slider(id={'type': 'dec-sliders', 'index': f'rad-slider-{stored_sliders[i]}'}, min=0, max=1, step=0.1, value=stored_sliders[i]))
        return tmp_sliders
    else:
        filtered = list(set([d['theta'] for d in radar_values['points']]))
        t = sorted([int(el.split('x')[1]) for el in filtered])
        new_sliders = []
        for i in range(len(filtered)):
            new_sliders.append(
                html.Div([
                    html.P(f"Decision Variable - {t[i]}", style={'fontSize': '18px'}),
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
#             new_sliders.append(html.P(f"Decision Variable - {t[i]}"))
#             new_sliders.append(dcc.Slider(id={'type': 'dec-sliders', 'index': f'rad-slider-{t[i]}'}, min=0, max=1, step=0.1, value=stored_sliders[t[i]-1]))
        return new_sliders

@app.callback(
    Output('radar-chart', 'figure'),
    Output('decision-values-store', 'data'),
    Output('slider-change-status', 'data', allow_duplicate=True),
    Input({
            "type": "dec-sliders",
            "index": ALL
        }, "value"),
    Input('radar-sliders', 'children'),
    Input('radar-chart', 'selectedData'),
    State('decision-values-store', 'data'),
    State('decision-variables-store', 'data'),
    prevent_initial_call=True
)

def update_radar(slider_values, slider_elements, radar_selected, slider_store, decision_vars):
#     print('update_radar', slider_store)
    th = decision_vars
    th.append(th[0])
#     print('th', th)

    triggered_id = [p['prop_id'] for p in ctx.triggered]
#     print('triggered_id', triggered_id)
    if 'radar-chart.selectedData' in triggered_id:
        return dash.no_update, dash.no_update, dash.no_update
#     elif 'rad-slider-' in triggered_id[0]:
#         return dash.no_update, dash.no_update, True
    else:
        if radar_selected is not None:
#             print(slider_values)
#             print(slider_store)
            filtered_labels = list(set([d['theta'] for d in radar_selected['points']]))
            filtered_labels_indices = [decision_vars.index(label) for label in filtered_labels]

            new_r = slider_store
            for i, x in enumerate(filtered_labels_indices):
                new_r[x] = slider_values[i]
            new_r.append(new_r[0])

            fig = go.Figure(data=go.Scatterpolar(
                r=new_r,
                theta=th,
                line_color='red'
            , selectedpoints=radar_selected))
            fig.update_layout(dragmode='select', margin=dict(l=20, r=20, t=20, b=20))
            return fig, new_r, dash.no_update

        else:
#             print(slider_values, 'me')
#             print(triggered_id, 'Check')
            new_r = slider_values
            new_r.append(new_r[0])
#             new_r.append(slider_values[0])
            fig = go.Figure(data=go.Scatterpolar(
                r=new_r,
                theta=th,
                line_color='red'
            ))
            fig.update_layout(dragmode='select', margin=dict(l=20, r=20, t=20, b=20))
            if 'rad-slider-' in triggered_id[0]:
                return fig, dash.no_update, True
        
            return fig, new_r, False





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
#                         print('checking', [float(x) for x in slider_values])
                        if num_decision_vars >= 5:
                            return [], [float(x) for x in slider_values]
                        return [float(x) for x in slider_values], []
                    
    return [0 for _ in slider_ids], [0 for _ in slider_ids]


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

def pareto_front(ds_slider_values, dec_slider_values, click_data, change_status, fig, data,
                 stored_slider_values, dims):
    slider_values = ds_slider_values
    if dims['dec'] >= 5:
        slider_values = dec_slider_values
        
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
            return fig
        # click_data = None
        n_var = dims['dec']
        n_obj = dims['obj']

        DTLZ2 = get_problem("dtlz2", n_var=n_var, n_obj=n_obj)
        dff = DTLZ2.evaluate(np.array([0 if x is None else x for x in slider_values ]))
        print('checking...', [0 if x is None else x for x in slider_values ], dff)
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
