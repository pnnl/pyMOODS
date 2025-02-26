import pandas as pd
import matplotlib as plt
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
from sklearn.cluster import DBSCAN, HDBSCAN

import vis

df = pd.read_csv('./v2_summary.csv')
df.head()

ovars = ['objective']
dvars = ['size', 'cable']
self = vis.Visualizer(data=df, data_ovars=ovars, data_dvars=dvars)

points = self.joint_xy

kwargs = dict(
        threshold=0.5,
        clu = HDBSCAN(
            cluster_selection_epsilon=1.,
            min_cluster_size=10
        ),
        drop_intermediate=False
    )

clusters = self.get_overlapping_clusters(**kwargs)

from scipy.spatial import ConvexHull
def get_convex_hull(points):
    # Drop duplicate points to avoid errors
    unique_points = points.drop_duplicates()

    # ConvexHull requires at least 3 points in 2D, 4 in 3D
    min_points = max(3, unique_points.shape[1] + 1)
    if unique_points.shape[0] < min_points:
        return unique_points  # Return all points if hull can't be computed

    try:
        hull = ConvexHull(unique_points.values)  # Compute convex hull
        return unique_points.iloc[hull.vertices]  # Return hull points
    except QhullError:
        return unique_points  # Return all points if convex hull fails

def draw_clusters_scatterplot(clusters, points, selected_indices=None):
    clusters = pd.get_dummies(clusters.iloc[:, 0], dtype=int).replace(0, -1)
    fig = go.Figure()
    no_cluster_mask = ~points.index.isin(clusters.index)
    no_cluster_df = points[no_cluster_mask]

    fig.add_trace(go.Scatter(x=no_cluster_df[0], y=no_cluster_df[1], mode='markers', marker=dict(color='lightgray', size=4, opacity=0.1), name='unassigned'))
    for i, c in enumerate(clusters):
        # if c in sorted(clusters.columns):
        ec = pc.hex_to_rgb(px.colors.qualitative.D3[i]) + (1.0,)
        hulls = [
            get_convex_hull(dfk)
            for k, dfk in points.groupby(clusters[c])
            if k != -1
        ]
        for j in range(len(hulls)):
            x_coords = hulls[j][0].to_list()
            y_coords = hulls[j][1].to_list()
            fig.add_trace(go.Scatter(x=x_coords+[x_coords[0]], y=y_coords+[y_coords[0]], mode="lines", fill="toself", fillcolor=f"rgba{ec[:3] + (0.2,)}", line=dict(color=f"rgba{ec}"), showlegend=False))

        mask = clusters[c] != -1
        # more than one item in that row with value other than -1
        multi_cluster_mask = (clusters[clusters.columns] != -1).sum(axis=1) > 1


        if selected_indices is not None:
            # mask for checking any data in subset created in dist plot
            selected_mask = clusters.index.isin(selected_indices)
            unselected_single_cluster_df = points.loc[clusters.index][mask & ~multi_cluster_mask & ~selected_mask]
            fig.add_trace(go.Scatter(x=unselected_single_cluster_df[0], y=unselected_single_cluster_df[1], mode='markers', marker=dict(color='lightgray', size=5, opacity=0.5), name=f'{c} (unselected)'))

            selected_single_cluster_df = points.loc[clusters.index][mask & ~multi_cluster_mask & selected_mask]
            fig.add_trace(go.Scatter(x=selected_single_cluster_df[0], y=selected_single_cluster_df[1], mode='markers', marker=dict(color=f'rgba{ec}', size=6), name=f'{c} (selected)'))

            # # points with multiple clusters
            unselected_multi_cluster_df = points.loc[clusters.index][multi_cluster_mask & ~selected_mask]
            fig.add_trace(go.Scatter(x=unselected_multi_cluster_df[0], y=unselected_multi_cluster_df[1], mode='markers', marker=dict(color='lightgray', size=5, opacity=0.5), name='multi_cluster (unselected)', showlegend=False if i > 0 else True))

            selected_multi_cluster_df = points.loc[clusters.index][multi_cluster_mask & selected_mask]
            fig.add_trace(go.Scatter(x=selected_multi_cluster_df[0], y=selected_multi_cluster_df[1], mode='markers', marker=dict(opacity=1, color='black', size=6), name='multi_cluster (selected)', showlegend=False if i > 0 else True))



        else:
            # excluding points with multiple clusters
            remaining_df = points.loc[clusters.index][mask & ~multi_cluster_mask]
            fig.add_trace(go.Scatter(x=remaining_df[0], y=remaining_df[1], mode='markers', marker=dict(color=f'rgba{ec}', size=5), name=c))

            # points with multiple clusters
            multi_cluster_df = points.loc[clusters.index][multi_cluster_mask]
            fig.add_trace(go.Scatter(x=multi_cluster_df[0], y=multi_cluster_df[1], mode='markers', marker=dict(color='black', size=5), name='multiple_cluster', showlegend=False))



    fig.update_layout(
        margin=dict(t=20, b=20),
        legend=dict(
            x=1.03,
            bordercolor='#d3d3d3',
            borderwidth=1,
            bgcolor='white',
            font=dict(
                size=14  # Set the font size of the legend items
            ),
            traceorder='normal',
            title=dict(text=' cluster', font=dict(size=14))
        ),
        # height=800,
        template="plotly_white",
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showticklabels=False, showgrid=False)
    )
    return fig

def assign_cluster_data(df, clusters, selected, dvars):
    y_name = clusters.columns[0]
    data = pd.concat([
        df.loc[clusters.index[clusters[c] == i], dvars]\
            .assign(**{y_name:i}, ovar=c)
        for c in clusters
        for i in clusters[c].unique()
        if i != -1
    ])

    return data

from plotly.subplots import make_subplots

def distplot_new(with_clusters, dvars, selected_info=[]):
    y = with_clusters['ovar'].values[0]
    df_with_clusters = pd.melt(with_clusters, id_vars=[y, 'ovar'], value_vars=dvars, var_name='dvar', ignore_index=False)\
        .reset_index()\
        .rename(columns={'index': 'orig_index'}).sort_values([y, 'dvar', 'ovar'])
    ovar = 'objective'
    colors = px.colors.qualitative.D3

    fig = make_subplots(rows=len(dvars), cols=1, shared_xaxes=False, vertical_spacing=0.05)

    for i, dvar in enumerate(dvars):
        row_mask = (df_with_clusters.dvar == dvar)
        if len(selected_info) == 0:
            data = df_with_clusters[row_mask]

            plot = go.Figure()
            plot.add_trace(
                go.Histogram(
                    x=data.value,
                    name=f"{ovar}",
                    marker=dict(color='#2874b4'),
                    nbinsx=100
                )
            )

            for trace in plot.data:
                trace.showlegend = (i==0)
                fig.add_trace(trace, row=i+1, col=1)
        else:
            if dvar in [d['row'] for d in selected_info]:
                selection = [d for d in selected_info if d['row'] == dvar]
                bounds = [selection[0]['bounds']['x0'], selection[0]['bounds']['x1']]
                data = df_with_clusters[row_mask]
                current = data.sort_values('value').reset_index(drop=True)

                selected_indices = current[current.value.between(bounds[0], bounds[1])].index

                plot = go.Figure()
                plot.add_trace(
                    go.Histogram(
                        x=current.value,
                        name='objective',
                        nbinsx=100,
                        marker=dict(color=colors[0]),
                        selectedpoints=selected_indices,
                        selected=dict(marker=dict(color='#2874b4')),
                        unselected=dict(marker=dict(color='lightgray'))
                    )
                )
                for trace in plot.data:
                    trace.showlegend = (i==0)
                    fig.add_trace(trace, row=i+1, col=1)


            # in the other rows
            else:
                filter_query = ''
                for idx in range(len(selected_info)):
                    row = selected_info[idx]['row']
                    curr_bounds = selected_info[idx]['bounds']

                    if idx == 0:
                        filter_query = f"({row} >= {curr_bounds['x0']}) and ({row} <= {curr_bounds['x1']})"
                    else:
                        filter_query += f"and ({row} >= {curr_bounds['x0']}) and ({row} <= {curr_bounds['x1']})"

                filtered = with_clusters.query(filter_query)
                with_clusters['active'] = with_clusters.index.isin(filtered.index)

                df_with_clusters = pd.melt(with_clusters, id_vars=[y, 'ovar', 'active'], value_vars=dvars, var_name='dvar', ignore_index=False)\
                    .reset_index()\
                    .rename(columns={'index': 'orig_index'}).sort_values([y, 'dvar', 'ovar'])

                data = df_with_clusters[row_mask]

                current = data.sort_values('value').reset_index(drop=True)
                plot = go.Figure()
                plot.add_trace(
                    go.Histogram(
                        x=current.value,
                        name='objective',
                        nbinsx=100,
                        marker=dict(color=colors[0]),
                        selectedpoints=current[current.active == True].index,
                        # selected=dict(marker=dict(color='#2874b4')),
                        unselected=dict(marker=dict(color='lightgray'))
                    )
                )

                for trace in plot.data:
                    trace.showlegend = (i==0)
                    fig.add_trace(trace, row=i+1, col=1)


    if len(selected_info) > 0:
        for j in range(len(selected_info)):
            row = selected_info[j]['row']
            bounds = selected_info[j]['bounds']

            fig.add_shape(
                dict(
                    {"type": "rect", "line": {"width": 1, "dash": "dot", "color": "darkgrey"}, 'xref': f'x{dvars.index(row)+1}', 'yref': f'y{dvars.index(row)+1}'},
                    **bounds
                )
            )


    # Add titles as annotations on the left of each subplot
    annotations = [
        dict(
            text="Count",  # Y-axis title text
            x=-0.08,  # Position relative to the figure (left side)
            y=0.5,  # Centered vertically
            xref="paper",  # Refer to the figure coordinates
            yref="paper",
            showarrow=False,
            textangle=-90,  # Rotate text vertically
            font=dict(size=16)  # Customize font size
        )
    ]

    for i, dvar in enumerate(dvars, start=1):
        annotations.append(
            dict(
                x=1.03,  # Position to the right of the plot area
                y=1.0-(i-0.5)*(1/len(dvars)),  # Center annotation for each subplot
                xref="paper",
                yref="paper",
                text=f"{dvar}",  # Bold text for titles
                showarrow=False,
                xanchor="right",
                yanchor="middle",
                font=dict(size=14),
                textangle=90
            ))
        fig.update_layout({
            f'xaxis{i}': dict(tickfont=dict(size=14)),
            f'yaxis{i}': dict(tickfont=dict(size=14))
        })


    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=10),
        yaxis=dict(titlefont=dict(size=20)),
        legend=dict(
            x=1.03,
            bordercolor='#d3d3d3',
            borderwidth=1,
            bgcolor='white',
            font=dict(
                size=14
            ),

            traceorder='normal',
            title=dict(text=' ovar', font=dict(size=14))
        ),
        barmode="stack",
        annotations=annotations,
        selectdirection='h', dragmode='select'
    )

    return fig

import numpy as np
def diverging_bar_chart(comp_df, a_name, b_name):
    group_a = comp_df.iloc[:, 0]
    group_b = comp_df.iloc[:, 1]

    max_abs_value = np.round(max(group_a.values + group_b.values), -2)
    if type(a_name) != str:
        a_name = str(int(a_name))
    if type(b_name) != str:
        b_name = str(int(b_name))

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=comp_df.index,
        x=[-x for x in group_a],
        name=a_name,
        orientation='h',
        marker=dict(color='rgba(0, 0, 255, 0.5)'),
        hovertemplate='<b>%{customdata[1]}</b><br>%{y}: %{customdata[0]}<extra></extra>',  # Custom hover template
        customdata=list(zip(group_a, [a_name] * len(group_a))),  # Custom data with name

    ))

    fig.add_trace(go.Bar(
        y=comp_df.index,
        x=group_b,
        name=b_name,
        orientation='h',
        marker=dict(color='rgba(255, 165, 0, 0.5)'),
        hovertemplate='<b>%{customdata[1]}</b><br>%{y}: %{customdata[0]}<extra></extra>',  # Custom hover template
        customdata=list(zip(group_b, [b_name] * len(group_b)))
    ))

    annot_right = []
    loc = 0.9
    for idx in comp_df.index:
        annot_right.append(
            dict(
                x=1,  # Position it slightly outside the chart (1 = right edge of plot)
                y=loc,  # Center vertically (normalized: 0 is bottom, 1 is top)
                xref="paper",  # Position relative to entire figure (not data space)
                yref="paper",
                text="{0:+.03f}".format(comp_df.loc[idx, 'diff']),  # Annotation text
                showarrow=False,  # No arrow
                font=dict(size=14, color="black"),
                align="left",
                xanchor='left'
            )
        )
        loc -= 0.25

    fig.update_layout(
        xaxis_title='Values',
        yaxis_title='dvar',
        barmode='overlay',
        bargap=0.1,
        showlegend=False,
        # xaxis=dict(
        #     tickvals=[-max_abs_value, -max_abs_value*0.75 -max_abs_value*0.5, -max_abs_value*0.25, 0, max_abs_value*0.25, max_abs_value*0.5, max_abs_value*0.75, max_abs_value],
        #     ticktext=[-max_abs_value, -max_abs_value*0.75, -max_abs_value*0.5, -max_abs_value*0.25, 0, max_abs_value*0.25, max_abs_value/2, max_abs_value*0.75,  max_abs_value],
        #     range=[-max_abs_value, max_abs_value]
        # ),
        yaxis=dict(autorange="reversed"),
        annotations=[
            dict(
                text=a_name,  # Text of the annotation
                xref="paper",  # Use "paper" to refer to the entire plotting area
                yref="paper",  # Use "paper" to refer to the entire plotting area
                x=0.2,  # X position (0.5 is the middle of the chart)
                y=1.15,  # Y position (1.1 places it above the chart)
                showarrow=False,  # Don't show an arrow
                font=dict(size=16)
            ),
            dict(
                text=b_name,  # Text of the annotation
                xref="paper",  # Use "paper" to refer to the entire plotting area
                yref="paper",  # Use "paper" to refer to the entire plotting area
                x=0.8,  # X position (0.5 is the middle of the chart)
                y=1.15,  # Y position (1.1 places it above the chart)
                showarrow=False,  # Don't show an arrow
                font=dict(size=16)
            ),

        ] + annot_right,
    )



    fig.add_shape(
        type="line",
        x0=0, y0=-1, x1=0, y1=len(comp_df),
        line=dict(color="black", width=2),
        xref="x", yref="y"
    )
    fig.update_layout(
        margin=dict(t=45),
        xaxis=dict(tickfont=dict(size=12)),
        yaxis=dict(tickfont=dict(size=12))
    )

    return fig

from dash import Dash, html, dcc, Output, Input, State, no_update, callback_context, dash_table
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

params = ['location', 'technology', 'duration', 'power']
points = self.joint_xy
all_clusters = self.get_overlapping_clusters(**kwargs)
init_with_clusters = assign_cluster_data(self.df, self.df[['location']], ['location'], dvars)
init_table_summary = init_with_clusters.iloc[:, :3].groupby(['location']).agg(['mean', 'std']).round(3)
init_table_summary.columns =  ['_'.join(col) for col in init_table_summary.columns]

app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                html.H6('Hyperparameters', style={'marginBottom': '0px', 'padding': '1% 1% 0% 1%',}),
                html.Div([
                    html.Div([
                        html.P('Location', style={'marginBottom': '0.5rem'}),
                        dcc.Dropdown(id='location-dropdown', options=sorted(self.df.location.unique()), value=[], multi=True)
                    ], style={'width': '24%'}),
                    html.Div([
                        html.P('Battery Technology', style={'marginBottom': '0.5rem'}),
                        dcc.Dropdown(id='technology-dropdown', options=sorted(self.df.technology.unique()), value=[], multi=True)
                    ], style={'width': '24%'}),
                    html.Div([
                        html.P('Battery Duration (hour)', style={'marginBottom': '0.5rem'}),
                        dcc.Dropdown(id='duration-dropdown', options=sorted(self.df.duration.unique()), value=[], multi=True)
                    ], style={'width': '24%'}),
                    html.Div([
                        html.P('Battery Power Rating (MW)', style={'marginBottom': '0.5rem'}),
                        dcc.Dropdown(id='power-dropdown', options=sorted(self.df.power.unique()), value=[], multi=True)
                    ], style={'width': '24%'})
                ], style={'display': 'flex', 'justifyContent': 'space-between',  'width': '50vw', 'padding': '1%'})
            ], style={'border': '1px solid #d3d3d3', 'marginRight': '1%'}),
            html.Div([
                html.Div([
                    html.H6('Color points by', style={'paddingTop': '1%', 'marginLeft': '2%', 'marginBottom': '5px'}),
                    dcc.Dropdown(id='color-var-dropdown', options=params+['clustering (DBSCAN)'], value='location', clearable=False, style={'paddingLeft': '2%', 'paddingRight': '2%', 'marginBottom': '1%'})
                ], style={'width': '30vw', 'border': '1px solid #d3d3d3'}),
                html.Div([
                    html.H6('Threshold (Epsilon)', style={'paddingTop': '1%', 'marginLeft': '2%', 'marginBottom': '5px'}),
                    dcc.Slider(0, 1, 0.1, value=kwargs['threshold'], id='th-slider')
                ], id='slider-container', style={'width': '30vw', 'border': '1px solid #d3d3d3', 'display': 'none'}),
            ], style={'display': 'flex', 'flexDirection': 'column'}),

        ], style={'display': 'flex', 'alignItems': 'flex-start'}),
        html.Div(dbc.Button('Reset', id='reset-select', outline=True, color='primary', n_clicks=0), style={'display': 'inline-block',}),
    ], style={'display': 'flex', 'padding': '5px', 'justifyContent': 'space-between'}),
    html.Div(id='graph-container', children=[
        html.Div([
            dcc.Loading(id='loading-1', children=[
                dcc.Graph(id='cluster-scatterplot',
                          figure=draw_clusters_scatterplot(self.df[['location']], points),
                          config={'displayModeBar': False}, style={'height': '50vh'})
            ]),
            html.Hr(),
            dcc.Loading(id='loading-2', children=[
                dash_table.DataTable(
                    id='data-table',
                    columns=[{'name': 'location', 'id': 'location'}, {'name': 'Battery size (MW)(mean)', 'id': 'size_mean'}, {'name': 'Battery size (MW)(std)', 'id': 'size_std'}, {'name': 'Cable size (MW)(mean)', 'id': 'cable_mean'}, {'name': 'Cable size (MW)(std)', 'id': 'cable_std'} ],
                    data=init_table_summary.reset_index().to_dict(orient='records'),
                    row_selectable="multi",
                    style_table={'width': '90%', 'marginTop': '1rem'},
                    selected_rows=[],
                    style_data_conditional=[],
                    page_size=10
                )
            ])
        ], style={'width': '50%'}),

        html.Div([
            dcc.Loading(id='loading-3',
                        children=dcc.Graph(id='obj-dec-histogram', figure=distplot_new(init_with_clusters, dvars),  style={'height': '50vh'})),
            html.Hr(),
            dcc.Loading(id='loading-4', children=dcc.Graph(id='diff-bar-chart', style={'height': '35vh'}))
        ], style={'width': '50%', 'height': '100%'})

    ], style={'display': 'flex', 'width': '100vw', 'height': '100vh'}),
    dcc.Store(id='selected-from-tbl', data=[]),
    dcc.Store(id='selected-hist-data-store', data=[])
])

@app.callback(
    Output('slider-container', 'style'),
    Output('data-table', 'columns'),
    Input('color-var-dropdown', 'value'),
    prevent_initial_call=True
)

def control_slider(colorby):
    common_dicts = [{'name': 'Battery size (MW)(mean)', 'id': 'size_mean'}, {'name': 'Battery size (MW)(std)', 'id': 'size_std'}, {'name': 'Cable size (MW)(mean)', 'id': 'cable_mean'}, {'name': 'Cable size (MW)(std)', 'id': 'cable_std'}]
    add = [{'name': colorby, 'id': colorby}]
    if colorby == 'clustering (DBSCAN)':
        add = [{'name': 'objective', 'id': 'objective'}]
        return {'width': '30vw', 'border': '1px solid #d3d3d3', 'display': 'block'}, add + common_dicts
    return {'width': '30vw', 'border': '1px solid #d3d3d3', 'display': 'none'}, add + common_dicts

@app.callback(
    Output('cluster-scatterplot', 'figure'),
    Output('obj-dec-histogram', 'figure'),
    Output('data-table', 'data'),
    Output('data-table', 'selected_rows'),
    Input('location-dropdown', 'value'),
    Input('technology-dropdown', 'value'),
    Input('duration-dropdown', 'value'),
    Input('power-dropdown', 'value'),
    Input('color-var-dropdown', 'value'),
    Input('th-slider', 'value'),
    Input('selected-hist-data-store', 'data'),
    prevent_initial_call=True
)

def update_plots_with_hyperparameters(sel_location, sel_technology, sel_duration, sel_power, colorby, th_value, selected_from_hist):
    changed_id = [p['prop_id'] for p in callback_context.triggered]

    kwargs = dict(
        threshold=th_value,
        clu = HDBSCAN(
            cluster_selection_epsilon=1.,
            min_cluster_size=10
        ),
        drop_intermediate=False
    )

    df = self.df.copy()
    if colorby == 'clustering (DBSCAN)':
        y = 'objective'
        curr_clusters = self.get_overlapping_clusters(**kwargs)
        df = self.df.loc[curr_clusters.index]
    else:
        y = colorby
        curr_clusters = df[[colorby]]

    location_filter, technology_filter, duration_filter, power_filter = df.location.unique(), df.technology.unique(), df.duration.unique(), df.power.unique()
    if len(sel_location) > 0:
        location_filter = sel_location
    if len(sel_technology) > 0:
        technology_filter = sel_technology
    if len(sel_duration) > 0:
        duration_filter = sel_duration
    if len(sel_power) > 0:
        power_filter = sel_power

    filtered = df[(df.location.isin(location_filter)) & (df.technology.isin(technology_filter)) & (df.duration.isin(duration_filter)) & (df.power.isin(power_filter))]
    updated_data_with_clusters = assign_cluster_data(self.df, curr_clusters.loc[filtered.index], curr_clusters.columns, dvars)
    data_table_summary = updated_data_with_clusters.iloc[:, :3].groupby([y]).agg(['mean', 'std']).round(3)
    data_table_summary.columns =  ['_'.join(col) for col in data_table_summary.columns]

    if 'selected-hist-data-store.data' in changed_id:
        if len(selected_from_hist) > 0:
            with_clusters_copy = updated_data_with_clusters.copy()
            filter_query=""
            for obj in selected_from_hist:
                filtered_dvar = obj['row']
                filtered_range = obj['bounds']
                if filter_query == '':
                    filter_query += f"({filtered_dvar} >= {filtered_range['x0']}) and ({filtered_dvar} <= {filtered_range['x1']})"
                else:
                    filter_query += f" and ({filtered_dvar} >= {filtered_range['x0']}) and ({filtered_dvar} <= {filtered_range['x1']})"

            with_clusters = with_clusters_copy.query(filter_query)
            data_table_summary = with_clusters.iloc[:, :3].groupby([y]).agg(['mean', 'std']).round(3)
            data_table_summary.columns =  ['_'.join(col) for col in data_table_summary.columns]
            return draw_clusters_scatterplot(curr_clusters.loc[filtered.index], points, with_clusters.index), distplot_new(updated_data_with_clusters, dvars, selected_from_hist), data_table_summary.reset_index().to_dict(orient='records'), no_update

    return draw_clusters_scatterplot(curr_clusters.loc[filtered.index], points), distplot_new(updated_data_with_clusters, dvars), data_table_summary.reset_index().to_dict(orient='records'), []

@app.callback(
    Output('selected-hist-data-store', 'data'),
    Input('obj-dec-histogram', 'selectedData'),
    Input('reset-select', 'n_clicks'),
    State('selected-hist-data-store', 'data'),
    State('th-slider', 'value'),
    State('color-var-dropdown', 'value'),
    prevent_initial_call=True
)

def save_selected_hist_data(selectedData, reset_click, curr_selected_data, th_value, colorby):
    changed_id = [p['prop_id'] for p in callback_context.triggered]
    kwargs = dict(
        threshold=th_value,
        clu = HDBSCAN(
            cluster_selection_epsilon=1.,
            min_cluster_size=10
        ),
        drop_intermediate=False
    )

    if colorby == 'clustering (DBSCAN)':
        y = 'objective'
        curr_clusters = self.get_overlapping_clusters(**kwargs)
    else:
        y = colorby
        curr_clusters = self.df[[colorby]]

    if 'reset-select.n_clicks' in changed_id:
        if selectedData:
            return []
        raise PreventUpdate
    if selectedData:
        updated_data_with_clusters = assign_cluster_data(self.df, curr_clusters, curr_clusters.columns, dvars)
        with_clusters_long = pd.melt(updated_data_with_clusters, id_vars=[y, 'ovar'], value_vars=self.dvars, var_name='dvar', ignore_index=False).reset_index()\
            .rename(columns={'index': 'orig_index'})

        if 'points' not in selectedData:
            return {}
        else:
            pts = selectedData['points']

            if len(pts) > 0:
                ranges = selectedData['range']

                x = [k for k in ranges.keys() if 'x' in k][0]
                y = [k for k in ranges.keys() if 'y' in k][0]

                if x=='x':
                    selected_row='x0'
                else:
                    selected_row = f"x{int(x[1])-1}"

                selection_bounds = {
                    "x0": ranges[x][0],
                    "x1": ranges[x][1],
                    "y0": ranges[y][0],
                    "y1": ranges[y][1],
                }

                range_mask = (with_clusters_long.value >= ranges[x][0]) & (with_clusters_long.value <= ranges[x][1])
                selected_row_mask = (with_clusters_long.dvar == selected_row)
                subset = with_clusters_long[selected_row_mask & range_mask]

                if len(curr_selected_data) == 0:
                    return [{'row': f"{dvars[int(selected_row.split('x')[1])]}", 'bounds': selection_bounds}]
                else:
                    current = curr_selected_data.copy()
                    current.append({'row': f"{dvars[int(selected_row.split('x')[1])]}", 'bounds': selection_bounds})
                    return current
    raise PreventUpdate


@app.callback(
    Output('data-table', 'style_data_conditional'),
    Output('selected-from-tbl', 'data'),
    Input('data-table', 'selected_rows'),
    State('data-table', 'data')
)

def handle_table_checkbox(selected_rows, data):
    if len(selected_rows) >= 2:
        style_data_conditional = [
            {
                "if": {"row_index": i},
                "pointer-events": "none",
                "opacity": "0.5"
            } for i in range(len(data)) if i not in selected_rows
        ]
    else:
        style_data_conditional = []

    return style_data_conditional, [data[i] for i in selected_rows]

@app.callback(
    Output('diff-bar-chart', 'style'),
    Output('diff-bar-chart', 'figure'),
    Input('selected-from-tbl', 'data'),
    State('color-var-dropdown', 'value'),
    prevent_initial_call=True
)

def draw_diff_chart(row_selected_store, colorby):
    if len(row_selected_store) == 2:
        d = pd.DataFrame(row_selected_store)
        if colorby == 'clustering (DBSCAN)':
            index_col='objective'
        else:
            index_col = colorby
        a, b = [d.iloc[0, :][index_col], d.iloc[1, :][index_col]]

        d.set_index(index_col, inplace=True)
        diff_row = d.iloc[1, :] - d.iloc[0, :]
        d = d._append(diff_row, ignore_index=True).T.rename(columns={2: 'diff'})

        return {'display': 'block', 'width': '100%', 'height': '35vh'}, diverging_bar_chart(d, a, b)
    else:
        return {'display': 'none'}, {}

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=3000)