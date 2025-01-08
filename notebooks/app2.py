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

def draw_clusters_in_dash(clusters, points, selected_indices=None):
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
        height=800,
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

def distplot_new(with_clusters, selected_clusters, selected_info=None):
    dvars = [c for c in with_clusters.columns if 'x' in c]
    df_with_clusters = pd.melt(with_clusters[with_clusters.ovar.isin(selected_clusters)], id_vars=['y', 'ovar'], value_vars=dvars, var_name='dvar', ignore_index=False)\
        .reset_index()\
        .rename(columns={'index': 'orig_index'}).sort_values(['y', 'dvar', 'ovar'])
    dvars = sorted(df_with_clusters.dvar.unique())
    ovars = sorted(df_with_clusters.ovar.unique())
    colors = px.colors.qualitative.D3

    fig = make_subplots(rows=len(dvars), cols=1, shared_xaxes=True, vertical_spacing=0.02)

    for i, dvar in enumerate(dvars):
        row_mask = (df_with_clusters.dvar == dvar)
        if selected_info is None:
            data = df_with_clusters[row_mask]
            plot = go.Figure()
            for ovar, color in zip(ovars, colors):
                plot.add_trace(
                    go.Histogram(
                        x=data[data["ovar"] == ovar]["value"],
                        name=f"{ovar}",  # Legend name
                        marker=dict(color=color), nbinsx=100  # Color for this category
                    )
                )

            for trace in plot.data:
                trace.showlegend = (i == 0)
                fig.add_trace(trace, row=i+1, col=1)
        else:
            bounds = [selected_info['bounds']['x0'], selected_info['bounds']['x1']]

            # in the filtered row
            if dvar == selected_info['row']:
                data = df_with_clusters[row_mask]

                plot = go.Figure()
                for ovar, color in zip(ovars, colors):
                    current = data[data.ovar == ovar].sort_values('value').reset_index(drop=True)
                    selected_indices = current[current.value.between(bounds[0], bounds[1])].index

                    plot.add_trace(
                        go.Histogram(
                            x=current.value,
                            name=ovar,
                            nbinsx=100,
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
                with_clusters['active'] = with_clusters.apply(lambda row: True if (row[selected_info['row']] >= bounds[0]) & (row[selected_info['row']] <= bounds[1]) else False, axis=1)
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
                            nbinsx=100,
                            marker=dict(color=color),
                            selectedpoints=selected_indices,
                            selected=dict(marker=dict(color=color)),
                            unselected=dict(marker=dict(color='lightgray'))
                        )
                    )

                for trace in plot.data:
                    trace.showlegend = (i==0)
                    fig.add_trace(trace, row=i+1, col=1)

    if selected_info is not None:
        row = selected_info['row']
        bounds = selected_info['bounds']
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
            x=-0.06,  # Position relative to the figure (left side)
            y=0.5,  # Centered vertically
            xref="paper",  # Refer to the figure coordinates
            yref="paper",
            showarrow=False,
            textangle=-90,  # Rotate text vertically
            font=dict(size=14)  # Customize font size
        )
    ]
    for i, dvar in enumerate(dvars, start=1):
        annotations.append(
            dict(
                x=1.03,  # Position to the right of the plot area
                y=1.0 - (i-0.5)*0.2,  # Center annotation for each subplot
                xref="paper",
                yref="paper",
                text=f"{dvar}",  # Bold text for titles
                showarrow=False,
                xanchor="right",
                yanchor="middle",
                font=dict(size=12),
                textangle=90
            ))

    fig.update_layout(
        margin=dict(t=20),
        legend=dict(
            x=1.03,
            # bordercolor='black',
            # borderwidth=1,
            bgcolor='#F5F5F5',
            font=dict(
                size=12  # Set the font size of the legend items
            ),
            traceorder='normal'
        ),
        barmode="stack",
        legend_title_text='ovar',
        annotations=annotations,
        selectdirection='h', dragmode='select'
    )
    return fig

from dash import Dash, html, dcc, Output, Input, State, no_update, callback_context
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
            html.P('Specialization (Cluster)', style={'marginBottom': '5px', 'padding': '1%'}),
            dcc.Dropdown(id='cluster-dropdown', placeholder='Select a cluster', options=all_clusters.columns, value=[sorted(all_clusters.columns)[0]], multi=True, style={'width': '40vw'})
        ], style={'border': '1px solid #d3d3d3', 'marginRight': '1%'}),
        html.Div([
            html.P('Threshold (Epsilon)', style={'marginLeft': '3%', 'marginBottom': '5px'}),
            dcc.Slider(0, 0.5, 0.1, value=0.3, id='th-slider')
        ], style={'width': '30vw', 'border': '1px solid #d3d3d3'}),
    ], style={'display': 'flex', 'padding': '5px'}),
    dcc.Loading(
        id='loading-1',
        children=
        html.Div(id='graph-container', children=[
            dcc.Graph(id='cluster-scatterplot', style={'width': '50%'}),
            html.Div([
                html.Div(dbc.Button('Reset', id='reset-select', outline=True, color='primary', n_clicks=0, style={'marginLeft': '5%'}), className="d-inline-block"),
                dcc.Graph(id='obj-dec-histogram', style={'width': '100%', 'height': '100%'})
            ], style={'width': '50%', 'height': '90vh', 'display': 'flex', 'flexDirection': 'column'})
        ], style={'display': 'none'})
    ),
    dcc.Store(id='clusters-store', data={}),
    dcc.Store(id='cluster-data-long-store', data={}),
    dcc.Store(id='selected-data-store', data={}),
    dcc.Store(id='tmp')

])

@app.callback(
    Output('cluster-scatterplot', 'figure'),
    Output('graph-container', 'style'),
    Output('obj-dec-histogram', 'figure'),
    Input('cluster-dropdown', 'value'),
    Input('th-slider', 'value')
)

def draw_figures(selected_clusters, th):
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
        with_clusters_long = pd.melt(with_clusters[with_clusters.ovar.isin(selected_clusters)], id_vars=['y', 'ovar'], value_vars=dvars, var_name='dvar', ignore_index=False)\
            .reset_index()\
            .rename(columns={'index': 'orig_index'}).sort_values(['y', 'dvar', 'ovar'])

        return draw_clusters_in_dash(clusters, points), {'display': 'flex'}, distplot_new(with_clusters, selected_clusters)
    else:
        return no_update, {'display': 'none'}, no_update

@app.callback(
    Output('cluster-scatterplot', 'figure', allow_duplicate=True),
    Output('selected-data-store', 'data'),
    Input('obj-dec-histogram', 'selectedData'),
    Input('reset-select', 'n_clicks'),
    State('cluster-dropdown', 'value'),
    prevent_initial_call=True
)

def update_selection(selectedData, reset_button, selected_clusters):
    changed_id = [p['prop_id'] for p in callback_context.triggered]
    clusters = self.get_overlapping_clusters(**kwargs)[sorted(selected_clusters)]
    if 'reset-select.n_clicks' in changed_id:
        if selectedData:
            return draw_clusters_in_dash(clusters, points), {}
        else:
            raise PreventUpdate
    if selectedData is None:
        # print(selectedData)
        raise PreventUpdate
    else:
        with_clusters = assign_cluster_data(self.df, clusters, clusters.columns)
        with_clusters_long = pd.melt(with_clusters[with_clusters.ovar.isin(selected_clusters)], id_vars=['y', 'ovar'], value_vars=dvars, var_name='dvar', ignore_index=False).reset_index()\
            .rename(columns={'index': 'orig_index'})

        pts = selectedData['points']
        if len(pts) > 0:
            ranges = selectedData['range']
            x = [k for k in ranges.keys() if 'x' in k][0]
            y = [k for k in ranges.keys() if 'y' in k][0]
            print(x, y)

            selected_row = f"x{int(x[1])-1}"
            print(selected_row)

            selection_bounds = {
                "x0": ranges[x][0],
                "x1": ranges[x][1],
                "y0": ranges[y][0],
                "y1": ranges[y][1],
            }

            range_mask = (with_clusters_long.value >= ranges[x][0]) & (with_clusters_long.value <= ranges[x][1])
            selected_row_mask = (with_clusters_long.dvar == selected_row)
            subset = with_clusters_long[selected_row_mask & range_mask]
            print({'row': selected_row, 'bounds': selection_bounds})

            return draw_clusters_in_dash(clusters, points, list(set(subset.orig_index))), {'row': selected_row, 'bounds': selection_bounds}

    raise PreventUpdate

@app.callback(
    Output('obj-dec-histogram', 'figure', allow_duplicate=True),
    Input('selected-data-store', 'data'),
    State('cluster-dropdown', 'value'),
    prevent_initial_call=True
)

def update_histogram(selected_data_store, selected_clusters):
    clusters = self.get_overlapping_clusters(**kwargs)[sorted(selected_clusters)]
    with_clusters = assign_cluster_data(self.df, clusters, clusters.columns)
    with_clusters_long = pd.melt(with_clusters[with_clusters.ovar.isin(selected_clusters)], id_vars=['y', 'ovar'], value_vars=dvars, var_name='dvar', ignore_index=False).reset_index()\
        .rename(columns={'index': 'orig_index'})

    if selected_data_store:
        return distplot_new(with_clusters, selected_clusters, selected_data_store)
    # raise PreventUpdate
    return distplot_new(with_clusters, selected_clusters)

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=5000)