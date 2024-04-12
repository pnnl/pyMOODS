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
import matplotlib.pyplot as plt

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


app.layout = html.Div([
    dcc.Store(id="slider-values-store", data={}),
    dcc.Store(id="slider-change-status", data={}), interface_layout
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

    summary_table = html.Table([
        html.Tr([
            html.Td(html.H3("SUMMARY"),
                    style={
                        'textAlign': 'center',
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
    ], style={'margin': '10rem auto auto auto',
        'fontWeight': '500',
        'borderRadius': '10px',
        'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.8)',
        'padding': '1.7rem',
        'fontFamily': 'Arial, Helvetica, sans-serif',
        'textAlign': 'center',
        'width': '82%',
        'display' : 'flex',
        'flexDirection' : 'column',
        'alignItems':'center'})

    return {'margin' : 'auto'}, summary_table


@app.callback(Output("graph1", "figure", allow_duplicate=True),
              Output("stored-df", "data"),
              Output("sliders", "children"),
              Output("slider-change-status", "data"), [
                  Input("upload-data", "contents"),
                  Input("upload-data", "filename"),
                  Input({
                      "type": "ds-sliders",
                      "index": ALL
                  }, "value"),
                  Input("graph1", "clickData")
              ],
              prevent_initial_call=True)
def update_output(contents, filename, slider_values, click_data):
    if contents is not None:
        contents = contents[0]
        filename = filename[0]
        df, decision_variables, objective_functions = parse_data(contents, filename)

    if df is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    changed_id = [p['prop_id'] for p in dash.callback_context.triggered]
    if len(changed_id) == len(decision_variables) + 1:
        return dash.no_update, dash.no_update, dash.no_update, False
    elif 'slider' in changed_id[0]:
        return dash.no_update, dash.no_update, dash.no_update, True
    elif click_data:
        return dash.no_update, dash.no_update, dash.no_update, False
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
    


@app.callback(
    [Output("mop-objective-graph", "figure"), Output("mop-decision-graph", "figure")],
    [Input("upload-data", "contents"),Input("upload-data", "filename")]
) 
def update_mop_graphs(contents, filename):
    if contents is None:
        return dash.no_update, dash.no_update
    
    content_type, content_string = contents[0].split(',')
    decoded = base64.b64decode(content_string)
    file = json.loads(decoded)

    df = pd.DataFrame(file)

    decision_variables = [col for col in df.columns if col.startswith('x')]
    objective_functions = [col for col in df.columns if col.startswith('f')]
    
    f1_values = np.linspace(df[objective_functions[0]].min(), df[objective_functions[0]].max(), 100)
    f2_values = np.linspace(df[objective_functions[1]].min(), df[objective_functions[1]].max(), 100)
    F1, F2 = np.meshgrid(f1_values, f2_values)
    
    objective_fig = go.Figure(data=[go.Surface(x=F1, y=F2,z=np.sqrt(F1**2 + F2**2), hovertemplate=
                            'f1: %{x}<br>f2: %{y}<br>f3: %{z}<extra></extra>')])
    # objective_fig = go.Figure(data=[go.Heatmap(z=df[objective_functions], colorscale='Viridis')])
    
    x1_values = np.linspace(df[decision_variables[0]].min(), df[decision_variables[0]].max(), 100)
    x2_values = np.linspace(df[decision_variables[1]].min(), df[decision_variables[1]].max(), 100)
    X1, X2 = np.meshgrid(x1_values, x2_values)
    
    decision_fig = go.Figure(data=[go.Surface(x=X1, y=X2,z=np.sqrt(X1**2 + X2**2), hovertemplate=
                            'x1: %{x}<br>x2: %{y}<br>x3: %{z}<extra></extra>')])
    # decision_fig = go.Figure(data=[go.Heatmap(z=df[decision_variables])])

    objective_fig.update_layout(
        scene=dict(
            xaxis = dict(title='f1', title_font=dict(size=24)),
            yaxis = dict(title='f2', title_font=dict(size=24)),
            zaxis = dict(title='f3', title_font=dict(size=24)),
            bgcolor = 'rgba(0,0,0,0)', 
        ),
        paper_bgcolor = 'rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0,t=0, b=100)
    )
    
    decision_fig.update_layout(
        scene=dict(
            xaxis = dict(title='x1', title_font=dict(size=24)),
            yaxis = dict(title='x2', title_font=dict(size=24)),
            zaxis = dict(title='x3', title_font=dict(size=24)),
            bgcolor = 'rgba(0,0,0,0)', 
        ),
        paper_bgcolor = 'rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0,t=0, b=100)
    )
    
    return objective_fig, decision_fig


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

                    if not dff.empty and len(slider_ids) > 0:
                        decision_variables = [
                            id['index'].split('-')[1] for id in slider_ids
                        ]
                        if pd.Series(decision_variables).isin(
                                dff.columns).all():
                            return list(dff[decision_variables].iloc[0])
                else:
                    trace_index = click_data["points"][0]["curveNumber"]
                    if 0 <= trace_index < len(df):
                        slider_values = df.iloc[
                            trace_index, :num_decision_vars].tolist()
                        
                        return slider_values

    return [0 for _ in slider_ids]

@app.callback(
    Output('graph1', "figure"),
    [
        Input({
            "type": "ds-sliders",
            "index": ALL
        }, "value"),
        Input('graph1', 'clickData'),
        Input('slider-change-status', 'data')
    ],
    [
        State('graph1', "figure"),
        State('stored-df', 'data'),
        State('slider-values-store', 'data'),
    ],
    prevent_initial_call=True)
def pareto_front(slider_values, click_data, change_status, fig, data,
                 stored_slider_values):
    if slider_values != stored_slider_values:
        stored_slider_values = slider_values
        print("Stored: ", stored_slider_values)
        if not slider_values or all(slider == 0 for slider in slider_values):
            return fig
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
        n_var = len(slider_values)
        n_obj = len(data[0]) - n_var
        DTLZ2 = get_problem("dtlz2", n_var=n_var, n_obj=n_obj)
        dff = DTLZ2.evaluate(np.array(slider_values))

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
        if click_data:
            if isinstance(fig.data[0], go.Scatter):
                f1_point = click_data['points'][0]['x']
                f2_point = click_data['points'][0]['y']
                fig.add_scatter(x=[f1_point],
                                y=[f2_point],
                                marker=dict(color='LightSeaGreen', size=30),
                                # text=f'f1: {f1_point: .2f}<br>f2: {f2_point: .2f}',
                                # hoverlabel=dict(font_size=22)
                                )
                # fig.update_traces(
                #      hovertemplate='f1: %{x}<br>f2: %{y}<extra></extra>')
            elif isinstance(fig.data[0], go.Scatter3d):
                f1_point = click_data['points'][0]['x']
                f2_point = click_data['points'][0]['y']
                f3_point = click_data['points'][0]['z']
                fig.add_scatter3d(x=[f1_point],
                                  y=[f2_point],
                                  z=[f3_point],
                                  mode='markers',
                                  marker=dict(color=f"rgb(32,178,170)", size=30),
                                  text=f'f1: {f1_point: .2f}<br>f2: {f2_point: .2f}<br>f3: {f3_point: .2f}',
                                  hoverlabel=dict(font_size=22))
                fig.update_traces(
                    hovertemplate=
                    'f1: %{x}<br>f2: %{y}<br>f3: %{z}<extra></extra>')
            elif isinstance(fig.data[0], go.Scatter):
                x_labels = [f'f{i+1}' for i in range(len(dff))]
                hover_text='<br>'.join([f'{label}: {value: .2f}' for label, value in zip(x_labels, dff) ])
                fig.add_scatter(
                    x=x_labels,
                    y=dff,
                    mode='lines+markers',
                    line=dict(color='red', width=5),
                    marker=dict(color='red', size=30, symbol='star'),
                    hoverinfo='text',
                    text=hover_text,
                    # text=f'f1: {dff[0]: .2f}<br>f2: {dff[1]: .2f}<br>f3: {dff[2]: .2f}<br>f4: {dff[3]: .2f}',
                    hoverlabel=dict(font_size=22))
                

    fig.update_layout(showlegend=False)
    return fig


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=5001)
