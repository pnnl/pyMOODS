import vis
import os
import pandas as pd
import matplotlib as plt
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
from sklearn.cluster import DBSCAN, HDBSCAN
from scipy.spatial import ConvexHull
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

path = "./dtlz2_d5_o5_p2000_g10000.json"
self = vis.Visualizer(from_path=path)

def get_convex_hull(points):
    return points.iloc[ConvexHull(points.values).vertices]

def draw_clusters_scatterplot(clusters, points, selected_indices=None):
    fig = go.Figure()
    no_cluster_mask = ~points.index.isin(clusters.index)
    no_cluster_df = points[no_cluster_mask]
    fig.add_trace(go.Scatter(x=no_cluster_df[0], y=no_cluster_df[1], mode='markers', marker=dict(color='lightgray', size=4, opacity=0.1), name='unassigned'))
    for i, c in enumerate(clusters):
        if c in sorted(clusters.columns):
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
        margin=dict(t=20),
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

def assign_cluster_data(df, clusters, selected):
    dvars = [c for c in df.columns if 'x' in c]
    data = pd.concat([
        df.loc[clusters.index[clusters[c] == i], dvars]\
            .assign(y=f'{c}-{i}', ovar=c)
        for c in clusters
        for i in clusters[c].unique()
        if i != -1
    ])

    return data

from plotly.subplots import make_subplots
from scipy.stats import gaussian_kde

def distplot_new(with_clusters, selected_clusters, selected_info=[]):
    dvars = [c for c in self.df.columns if 'x' in c]
    df_with_clusters = pd.melt(with_clusters[with_clusters.ovar.isin(selected_clusters)], id_vars=['y', 'ovar'], value_vars=dvars, var_name='dvar', ignore_index=False)\
        .reset_index()\
        .rename(columns={'index': 'orig_index'}).sort_values(['y', 'dvar', 'ovar'])
    dvars = sorted(df_with_clusters.dvar.unique())
    ovars = sorted(df_with_clusters.ovar.unique())
    colors = px.colors.qualitative.D3

    fig = make_subplots(rows=len(dvars), cols=1, shared_xaxes=True, vertical_spacing=0.02)

    for i, dvar in enumerate(dvars):
        row_mask = (df_with_clusters.dvar == dvar)
        if len(selected_info) == 0:
            data = df_with_clusters[row_mask]
            plot = go.Figure()
            for ovar, color in zip(ovars, colors):
                plot.add_trace(
                    go.Histogram(
                        x=data[data["ovar"] == ovar]["value"],
                        name=f"{ovar}",  # Legend name
                        marker=dict(color=color), nbinsx=len(dvars)*10  # Color for this category
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

                plot = go.Figure()
                for ovar, color in zip(ovars, colors):
                    current = data[data.ovar == ovar].sort_values('value').reset_index(drop=True)
                    selected_indices = current[current.value.between(bounds[0], bounds[1])].index

                    plot.add_trace(
                        go.Histogram(
                            x=current.value,
                            name=ovar,
                            nbinsx=len(dvars)*10,
                            marker=dict(color=color),
                            selectedpoints=selected_indices,
                            selected=dict(marker=dict(color=color)),
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

                filtered = with_clusters.query(filter_query).index
                # print(filtered)
                # with_clusters['active'] = with_clusters.apply(lambda row: (row[selected_info[-1]['row']] >= bounds[0]) & (row[selected_info[-1]['row']] <= bounds[1]), axis=1)
                with_clusters['active'] = with_clusters.index.isin(filtered)

                df_with_clusters = pd.melt(with_clusters[with_clusters.ovar.isin(selected_clusters)], id_vars=['y', 'ovar', 'active'], value_vars=dvars, var_name='dvar', ignore_index=False)\
                    .reset_index()\
                    .rename(columns={'index': 'orig_index'}).sort_values(['y', 'dvar', 'ovar'])


                data = df_with_clusters[row_mask]

                plot = go.Figure()
                for ovar, color in zip(ovars, colors):
                    current = data[data.ovar == ovar].sort_values('value').reset_index(drop=True)
                    selected_indices = current[current.active == True].index
                    plot.add_trace(
                        go.Histogram(
                            x=current.value,
                            name=ovar,
                            nbinsx=len(dvars)*10,
                            marker=dict(color=color),
                            selectedpoints=selected_indices,
                            selected=dict(marker=dict(color=color)),
                            unselected=dict(marker=dict(color='lightgray'))
                        )
                    )

                for trace in plot.data:
                    trace.showlegend = (i==0)
                    fig.add_trace(trace, row=i+1, col=1)


    if len(selected_info) > 0:
        for i in range(len(selected_info)):
            row = selected_info[i]['row']
            bounds = selected_info[i]['bounds']
            fig.add_shape(
                dict(
                    {"type": "rect", "line": {"width": 1, "dash": "dot", "color": "darkgrey"}, 'yref': f'y{int(row[1])+1}'},
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
        margin=dict(t=20),
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


from dash import Dash, html, dcc, Output, Input, State, no_update, callback_context, dash_table
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

kwargs = dict(
            threshold=0.3,
            clu = HDBSCAN(
                cluster_selection_epsilon=1.,
                min_cluster_size=10
            ),
            drop_intermediate=False
        )
points = self.joint_xy
all_clusters = self.get_overlapping_clusters(**kwargs)
dvars = [c for c in self.df.columns if 'x' in c]

app.layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
               html.H6('Specialization (Cluster)', style={'marginBottom': '5px', 'padding': '1%'}),
               dcc.Dropdown(id='cluster-dropdown', placeholder='Select a cluster', options=all_clusters.columns, value=[sorted(all_clusters.columns)[0]], multi=True, style={'width': '40vw'})
            ], style={'border': '1px solid #d3d3d3', 'marginRight': '1%'}),
            html.Div([
                html.H6('Threshold (Epsilon)', style={'paddingTop': '1%', 'marginLeft': '3%', 'marginBottom': '5px'}),
                dcc.Slider(0, 0.5, 0.1, value=0.3, id='th-slider')
            ], style={'width': '30vw', 'border': '1px solid #d3d3d3'}),
        ], style={'display': 'flex'}),
        html.Div(dbc.Button('Reset', id='reset-select', outline=True, color='primary', n_clicks=0), style={'display': 'inline-block',}),
    ], style={'display': 'flex', 'padding': '5px', 'justifyContent': 'space-between'}),
    html.Div(id='graph-container', children=[
        html.Div([
            dcc.Loading(id='loading-1', children=[
                dcc.Graph(id='cluster-scatterplot', config={'displayModeBar': False}, style={'height': '50vh'})
            ]),
            html.Hr(),
            dcc.Loading(id='loading-2', children=[
                dash_table.DataTable(
                    id='data-table',
                    columns=[{'name': i, 'id': i} for i in ['ovar'] + [c for c in self.df.columns if c.startswith('x') ]],
                    row_selectable="multi",
                    style_table={'width': '90%', 'marginTop': '1rem'},
                    selected_rows=[],
                    style_data_conditional=[],
                    page_size=10
                )
            ])
        ], style={'width': '50%'}),

        html.Div([
            dcc.Loading(id='loading-3', children=dcc.Graph(id='obj-dec-histogram', style={'height': '50vh'})),
            html.Hr(),
            dcc.Loading(id='loading-4', children=dcc.Graph(id='diff-bar-chart', style={'height': '35vh'}))
        ], style={'width': '50%', 'height': '100%'})

    ], style={'display': 'flex', 'width': '100vw', 'height': '100vh'}),

    dcc.Store(id='selected-hist-data-store', data=[]),
    dcc.Store(id='selected-from-tbl', data=[])
])

@app.callback(
    Output('cluster-scatterplot', 'figure'),
    Output('obj-dec-histogram', 'figure'),
    Output('data-table', 'data'),
    Output('data-table', 'selected_rows'),
    Input('cluster-dropdown', 'value'),
    Input('th-slider', 'value'),
    Input('selected-hist-data-store', 'data')
)

def draw_figures(selected_clusters, th, selected_from_hist):
    changed_id = [p['prop_id'] for p in callback_context.triggered]
    output = []
    if len(selected_clusters) > 0:
        kwargs = dict(
            threshold=th,
            clu = HDBSCAN(
                cluster_selection_epsilon=1.,
                min_cluster_size=10
            ),
            drop_intermediate=False
        )
        # `clusters` variable updates when selected specialization cluster on dropdown changes
        clusters = self.get_overlapping_clusters(**kwargs)[sorted(selected_clusters)]
        with_clusters = assign_cluster_data(self.df, clusters, clusters.columns)

        if 'th-slider.value' in changed_id:
            return draw_clusters_scatterplot(clusters, points), distplot_new(with_clusters, selected_clusters), no_update, []
        if selected_from_hist:
            with_clusters_copy = with_clusters.copy()
            filter_query=""
            for obj in selected_from_hist:
                filtered_dvar = obj['row']
                filtered_range = obj['bounds']
                if filter_query == '':
                    filter_query += f"({filtered_dvar} >= {filtered_range['x0']}) and ({filtered_dvar} <= {filtered_range['x1']})"
                else:
                    filter_query += f" and ({filtered_dvar} >= {filtered_range['x0']}) and ({filtered_dvar} <= {filtered_range['x1']})"

            with_clusters = with_clusters_copy.query(filter_query)
        # print(with_clusters.shape)
        # with_clusters_long = pd.melt(with_clusters[with_clusters.ovar.isin(selected_clusters)], id_vars=['y', 'ovar'], value_vars=self.dvars, var_name='dvar', ignore_index=False)\
        #     .reset_index()\
        #     .rename(columns={'index': 'orig_index'}).sort_values(['y', 'dvar', 'ovar'])

        cols = ['ovar'] + self.dvars
        for cluster in selected_clusters:
            subset = with_clusters[with_clusters.ovar == cluster][cols].round(4).sample(n=5)
            output = output + subset.to_dict(orient='records')
        if selected_from_hist:
            return draw_clusters_scatterplot(clusters, points, list(set(with_clusters.index))), distplot_new(with_clusters, selected_clusters), output, []
        else:
            return draw_clusters_scatterplot(clusters, points), distplot_new(with_clusters, selected_clusters), output, []
    else:
        return no_update, no_update, no_update, []

@app.callback(
    Output('cluster-scatterplot', 'figure', allow_duplicate=True),
    Output('selected-hist-data-store', 'data'),
    Input('obj-dec-histogram', 'selectedData'),
    Input('reset-select', 'n_clicks'),
    Input('cluster-dropdown', 'value'),
    State('selected-hist-data-store', 'data'),
    prevent_initial_call=True
)

def update_selection(selectedData, reset_button, selected_clusters, curr_selected_data):
    changed_id = [p['prop_id'] for p in callback_context.triggered]
    clusters = self.get_overlapping_clusters(**kwargs)[sorted(selected_clusters)]
    if 'cluster-dropdown.value' in changed_id:
        return no_update, []
    if 'reset-select.n_clicks' in changed_id:
        if selectedData:
            return draw_clusters_scatterplot(clusters, points), []
        else:
            raise PreventUpdate
    if selectedData is None:
        raise PreventUpdate
    else:
        with_clusters = assign_cluster_data(self.df, clusters, clusters.columns)
        with_clusters_long = pd.melt(with_clusters[with_clusters.ovar.isin(selected_clusters)], id_vars=['y', 'ovar'], value_vars=self.dvars, var_name='dvar', ignore_index=False).reset_index()\
            .rename(columns={'index': 'orig_index'})
        if 'points' not in selectedData:
            return draw_clusters_scatterplot(clusters, points), {}
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
                return draw_clusters_scatterplot(clusters, points, list(set(subset.orig_index))), [{'row': selected_row, 'bounds': selection_bounds}]
            else:
                current = curr_selected_data.copy()
                current.append({'row': selected_row, 'bounds': selection_bounds})
            return draw_clusters_scatterplot(clusters, points, list(set(subset.orig_index))), current

    raise PreventUpdate


@app.callback(
    Output('obj-dec-histogram', 'figure', allow_duplicate=True),
    Input('selected-hist-data-store', 'data'),
    State('cluster-dropdown', 'value'),
    prevent_initial_call=True
)

def update_histogram(selected_data_store, selected_clusters):
    changed_id = [p['prop_id'] for p in callback_context.triggered]

    clusters = self.get_overlapping_clusters(**kwargs)[sorted(selected_clusters)]
    with_clusters = assign_cluster_data(self.df, clusters, clusters.columns)
    with_clusters_long = pd.melt(with_clusters[with_clusters.ovar.isin(selected_clusters)], id_vars=['y', 'ovar'], value_vars=self.dvars, var_name='dvar', ignore_index=False).reset_index()\
        .rename(columns={'index': 'orig_index'})
    if selected_data_store:

        return distplot_new(with_clusters, selected_clusters, selected_data_store)
    return distplot_new(with_clusters, selected_clusters)

@app.callback(
    Output('data-table', 'style_data_conditional'),
    Output('selected-from-tbl', 'data'),
    Input('data-table', 'selected_rows'),
    State('data-table', 'data')
)

def handle_checkbox(selected_rows, data):
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
    prevent_initial_call=True
)

def draw_diff_chart(row_selected_store):
    if len(row_selected_store) == 2:
        d = pd.DataFrame(row_selected_store)
        d.set_index('ovar', inplace=True)
        diff_row = d.iloc[1, :] - d.iloc[0, :]
        d = d._append(diff_row, ignore_index=True).T.rename(columns={2: 'diff'})

        return {'display': 'block', 'width': '100%', 'height': '35vh'}, diverging_diff_plot(d.sort_values('diff', ascending=False))
    else:
        return {'display': 'none'}, {}

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=5000)