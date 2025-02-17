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
    clusters = pd.get_dummies(clusters['objective'], dtype=int).replace(0, -1)
    fig = go.Figure()
    no_cluster_mask = ~points.index.isin(clusters.index)
    no_cluster_df = points[no_cluster_mask]
    # print(no_cluster_mask)
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
    # dvars = [c for c in self.df.columns if 'x' in c]

    data = pd.concat([
        df.loc[clusters.index[clusters[c] == i], dvars]\
            .assign(y=f'{c}-{i}', ovar=c)
        for c in clusters
        for i in clusters[c].unique()
        if i != -1
    ])

    return data

from plotly.subplots import make_subplots

def distplot_new(with_clusters, dvars, selected_info=[]):
    # dvars = [c for c in self.df.columns if 'x' in c]
    df_with_clusters = pd.melt(with_clusters, id_vars=['y', 'ovar'], value_vars=dvars, var_name='dvar', ignore_index=False)\
        .reset_index()\
        .rename(columns={'index': 'orig_index'}).sort_values(['y', 'dvar', 'ovar'])
    dvars = sorted(df_with_clusters.dvar.unique())
    ovars = sorted(df_with_clusters.ovar.unique())
    colors = px.colors.qualitative.D3

    fig = make_subplots(rows=len(dvars), cols=1, shared_xaxes=False, vertical_spacing=0.05)

    for i, dvar in enumerate(dvars):
        row_mask = (df_with_clusters.dvar == dvar)
        if len(selected_info) == 0:
            data = df_with_clusters[row_mask]
            plot = go.Figure()
            for ovar, color in zip(ovars, colors):
                plot.add_trace(
                    go.Histogram(
                        x=data[data["ovar"] == ovar]["value"],
                        name=f"{ovar}",
                        marker=dict(color=color),
                        nbinsx=len(dvars)*10
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
def diverging_diff_plot(df_with_diff):
    differences = df_with_diff['diff']

    max_abs_value = np.round(max(list(map(abs, differences))), 1)

    positive_differences = [max(0, diff) for diff in differences]
    negative_differences = [min(0, diff) for diff in differences]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df_with_diff.index,
        x=positive_differences,
        name='Solution B > Solution A',
        orientation='h',
        marker=dict(color='green')
    ))

    fig.add_trace(go.Bar(
        y=df_with_diff.index,
        x=negative_differences,
        name='Solution B < Solution A',
        orientation='h',
        marker=dict(color='red')
    ))

    fig.update_layout(
        # title='Diverging Bar Chart: Differences (Solution B - Solution A)',
        xaxis_title='Difference (Solution B - Solution A)',
        yaxis_title='dvar',
        barmode='relative',
        bargap=0.1,
        showlegend=True,
        xaxis=dict(
            tickvals=[-max_abs_value, -max_abs_value/2, 0, max_abs_value/2, max_abs_value],
            ticktext=[max_abs_value, max_abs_value/2, 0, max_abs_value/2, max_abs_value],
            range=[-max_abs_value, max_abs_value]
        ),
        yaxis=dict(autorange="reversed")
    )

    fig.add_shape(
        type="line",
        x0=0, y0=-1, x1=0, y1=len(df_with_diff),
        line=dict(color="black", width=2),
        xref="x", yref="y"
    )
    fig.update_layout(margin=dict(t=20))
    fig.update_yaxes(showticklabels=True, ticks="outside")  # Show tick marks outside the axis

    return fig

from dash import Dash, html, dcc, Output, Input, State, no_update, callback_context, dash_table
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

points = self.joint_xy
all_clusters = self.get_overlapping_clusters(**kwargs)

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
                # dcc.Dropdown(id='cluster-dropdown', placeholder='Select a cluster', options=all_clusters.columns, value=[sorted(all_clusters.columns)[0]], multi=True, style={'width': '40vw'})
            ], style={'border': '1px solid #d3d3d3', 'marginRight': '1%'}),
            html.Div([
                html.H6('Threshold (Epsilon)', style={'paddingTop': '1%', 'marginLeft': '3%', 'marginBottom': '5px'}),
                dcc.Slider(0, 1, 0.1, value=1, id='th-slider')
            ], style={'width': '30vw', 'border': '1px solid #d3d3d3'}),
        ], style={'display': 'flex', 'alignItems': 'flex-start'}),
        html.Div(dbc.Button('Reset', id='reset-select', outline=True, color='primary', n_clicks=0), style={'display': 'inline-block',}),
    ], style={'display': 'flex', 'padding': '5px', 'justifyContent': 'space-between'}),
    html.Div(id='graph-container', children=[
        html.Div([
            dcc.Loading(id='loading-1', children=[
                dcc.Graph(id='cluster-scatterplot',
                          figure=draw_clusters_scatterplot(all_clusters, points),
                          config={'displayModeBar': False}, style={'height': '50vh'})
            ]),
            html.Hr(),
            dcc.Loading(id='loading-2', children=[
                dash_table.DataTable(
                    id='data-table',
                    columns=[{'name': i, 'id': i} for i in ['ovar'] + self.dvars],
                    data=assign_cluster_data(self.df, all_clusters, all_clusters.columns, dvars)[['ovar'] + dvars].round(4).sample(n=5).to_dict(orient='records'),
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
                        children=dcc.Graph(id='obj-dec-histogram', figure=distplot_new(assign_cluster_data(self.df, all_clusters, all_clusters.columns, dvars), dvars),  style={'height': '50vh'})),
            html.Hr(),
            dcc.Loading(id='loading-4', children=dcc.Graph(id='diff-bar-chart', style={'height': '35vh'}))
        ], style={'width': '50%', 'height': '100%'})

    ], style={'display': 'flex', 'width': '100vw', 'height': '100vh'}),
    dcc.Store(id='selected-from-tbl', data=[])

])

@app.callback(
    Output('cluster-scatterplot', 'figure'),
    Output('obj-dec-histogram', 'figure'),
    Output('data-table', 'data'),
    Input('location-dropdown', 'value'),
    Input('technology-dropdown', 'value'),
    Input('duration-dropdown', 'value'),
    Input('power-dropdown', 'value'),
    prevent_initial_call=True
)

def update_scatterplot_with_hyperparameters(sel_location, sel_technology, sel_duration, sel_power):
    df = self.df.loc[all_clusters.index]
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
    updated_data_with_clusters = assign_cluster_data(self.df, all_clusters.loc[filtered.index], all_clusters.columns, dvars)

    return draw_clusters_scatterplot(all_clusters.loc[filtered.index], points), distplot_new(updated_data_with_clusters, dvars), updated_data_with_clusters[['ovar'] + dvars].round(4).sample(n=5).to_dict(orient='records')

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
    app.run_server(debug=True, host="0.0.0.0", port=3000)