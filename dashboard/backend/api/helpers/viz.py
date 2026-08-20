"""Plotly figure-building helpers."""
import pandas as pd
import plotly.colors as pc
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from scipy.spatial import ConvexHull
from scipy.spatial.qhull import QhullError


def get_convex_hull(points: pd.DataFrame) -> pd.DataFrame:
    unique = points.drop_duplicates()
    min_pts = max(3, unique.shape[1] + 1)
    if unique.shape[0] < min_pts:
        return unique
    try:
        return unique.iloc[ConvexHull(unique.values).vertices]
    except QhullError:
        return unique


def rgba_with_opacity(rgb_hex: str, opacity: float = 1.0) -> str:
    r, g, b = pc.hex_to_rgb(rgb_hex)
    return f"rgba({r}, {g}, {b}, {opacity})"


def draw_clusters_scatterplot(full_dataset, points, clusters, objective_keys, color_by=None, size=None):
    fig = go.Figure()
    obj_frame = full_dataset[objective_keys]

    # ── Unassigned (grey) points ───────────────────────────────────────────
    no_cluster = points[~points.index.isin(clusters.index)]
    no_cluster_obj = obj_frame.loc[no_cluster.index]
    hover = ['<br>'.join(f'<b>{c.title()}:</b> {r[c]}' for c in obj_frame.columns)
             for _, r in no_cluster_obj.iterrows()]
    fig.add_trace(go.Scatter(
        x=no_cluster[0], y=no_cluster[1], mode='markers',
        marker=dict(color='lightgray', size=4, opacity=0.3),
        name='Unassigned', hoverinfo='text', hovertext=hover,
    ))

    clustering = pd.get_dummies(clusters.iloc[:, 0], dtype=int).replace(0, -1)
    use_coloring = color_by in full_dataset.columns
    color_map: dict = {}
    seen_legend: set = set()
    if use_coloring:
        palette = pc.qualitative.D3
        for i, val in enumerate(full_dataset[color_by].dropna().unique()):
            color_map[val] = rgba_with_opacity(palette[i % len(palette)], 1.0)

    for i, c in enumerate(clustering.columns):
        mask = clustering[c] != -1
        c_idx = clustering.index[mask]
        c_pts = points.loc[c_idx]
        c_obj = full_dataset.loc[c_idx]
        gen_mask = (clustering[clustering.columns] != -1).sum(axis=1) > 1

        if isinstance(size, pd.Series):
            sz = size.loc[c_idx]
            diff = max(abs(sz.max() - sz.min()), 1)
            sz = (sz - sz.min()) / diff * 30 + 5
        else:
            sz = pd.Series(10, index=c_idx)

        if use_coloring:
            color_col = full_dataset.loc[c_idx, color_by]
            for val in color_col.unique():
                idx = color_col[color_col == val].index
                sub_pts = c_pts.loc[idx]
                sub_obj = c_obj.loc[idx]
                hover = ['<br>'.join(f'<b>{col.title()}:</b> {r[col]}' for col in obj_frame.columns)
                         for _, r in sub_obj.iterrows()]
                fig.add_trace(go.Scatter(
                    x=sub_pts[0], y=sub_pts[1], mode='markers',
                    marker=dict(color=color_map[val], size=sz.loc[idx]),
                    name=str(val), legendgroup=str(val),
                    hoverinfo='text', hovertext=hover,
                    showlegend=(val not in seen_legend),
                ))
                seen_legend.add(val)
        else:
            hover = ['<br>'.join(f'<b>{col.title()}:</b> {r[col]}' for col in obj_frame.columns)
                     for _, r in c_obj.iterrows()]
            fig.add_trace(go.Scatter(
                x=c_pts[0], y=c_pts[1], mode='markers',
                marker=dict(color=pc.qualitative.D3[i % len(pc.qualitative.D3)], size=sz),
                name=c, hoverinfo='text', hovertext=hover,
            ))

        generalizers = c_pts[gen_mask]
        if not generalizers.empty:
            fig.add_trace(go.Scatter(
                x=generalizers[0], y=generalizers[1], mode='markers',
                marker=dict(color='black', size=sz.loc[generalizers.index]),
                name='Generalizers', showlegend=(i == 0),
            ))

    x_min, x_max = points[0].min(), points[0].max()
    y_min, y_max = points[1].min(), points[1].max()
    xb = 0.15 * (x_max - x_min)
    yb = 0.15 * (y_max - y_min)

    fig.update_layout(
        title="", margin=dict(t=0, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="top", y=0, xanchor="center", x=0.5,
                    bgcolor='white', bordercolor='#d3d3d3', borderwidth=1,
                    font=dict(size=10), itemwidth=30, traceorder='normal', itemsizing='constant'),
        template="plotly_white",
        xaxis=dict(range=[x_min - xb, x_max + xb], autorange=False, visible=False),
        yaxis=dict(range=[y_min - yb, y_max + yb], autorange=False, visible=False),
        shapes=[{'type': 'rect', 'xref': 'paper', 'yref': 'paper',
                 'x0': 0, 'y0': 0, 'x1': 1, 'y1': 1,
                 'line': {'color': '#999', 'width': 1.5, 'dash': 'solid'},
                 'fillcolor': 'rgba(255,255,255,0)'}],
        hovermode='closest', showlegend=True, height=300, autosize=True,
    )
    fig.update_traces(hoverlabel=dict(bgcolor="white", font_size=12))
    return fig


def generate_stacked_histogram(filtered_data: pd.DataFrame):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=False, vertical_spacing=0.15)
    fig.add_trace(go.Histogram(x=filtered_data['size'],  marker=dict(color='skyblue'), name='Size'),  row=1, col=1)
    fig.add_trace(go.Histogram(x=filtered_data['cable'], marker=dict(color='skyblue'), name='Cable'), row=2, col=1)
    fig.update_layout(
        margin=dict(l=5, r=0),
        grid=dict(rows=2, columns=1, pattern='independent'),
        title='Decision Space',
        xaxis=dict(dtick=20),
        yaxis=dict(title='Size', dtick=5, range=[0, 25]),
        xaxis2=dict(dtick=200),
        yaxis2=dict(title='Cable', tickmode='linear', dtick=10, range=[0, 40]),
    )
    return fig


def distplot_new(with_clusters, dvars: list, selected_info: list = []):
    y = with_clusters['ovar'].iloc[0]
    colors = px.colors.qualitative.D3

    def _melt(df):
        return (
            pd.melt(df, id_vars=[c for c in [y, 'ovar', 'active'] if c in df.columns],
                    value_vars=dvars, var_name='dvar', ignore_index=False)
            .reset_index().rename(columns={'index': 'orig_index'})
            .sort_values([y, 'dvar', 'ovar'])
        )

    df_melt = _melt(with_clusters)
    fig = make_subplots(rows=len(dvars), cols=1, shared_xaxes=False, vertical_spacing=0.13)

    for i, dvar in enumerate(dvars):
        row_mask = df_melt.dvar == dvar
        if not selected_info:
            data = df_melt[row_mask]
            fig.add_trace(go.Histogram(
                x=data.value, name='objective', marker=dict(color='#2874b4'),
                nbinsx=100, showlegend=(i == 0),
                hovertemplate='Objective: %{x}<extra></extra>',
            ), row=i + 1, col=1)
        elif dvar in [d['row'] for d in selected_info]:
            sel = next(d for d in selected_info if d['row'] == dvar)
            bounds = [sel['bounds']['x0'], sel['bounds']['x1']]
            current = df_melt[row_mask].sort_values('value').reset_index(drop=True)
            fig.add_trace(go.Histogram(
                x=current.value, name='objective', nbinsx=100, marker=dict(color=colors[0]),
                selectedpoints=current[current.value.between(*bounds)].index,
                selected=dict(marker=dict(color='#2874b4')),
                unselected=dict(marker=dict(color='lightgray')),
                hovertemplate='Objective: %{x}<extra></extra>', showlegend=(i == 0),
            ), row=i + 1, col=1)
        else:
            q = ' and '.join(
                f"({d['row']} >= {d['bounds']['x0']}) and ({d['row']} <= {d['bounds']['x1']})"
                for d in selected_info
            )
            filtered = with_clusters.query(q)
            with_clusters['active'] = with_clusters.index.isin(filtered.index)
            df_melt = _melt(with_clusters)
            current = df_melt[df_melt.dvar == dvar].sort_values('value').reset_index(drop=True)
            fig.add_trace(go.Histogram(
                x=current.value, name='objective', nbinsx=100, marker=dict(color=colors[0]),
                selectedpoints=current[current.active].index,
                unselected=dict(marker=dict(color='lightgray')), showlegend=(i == 0),
            ), row=i + 1, col=1)

    if selected_info:
        for info in selected_info:
            row = info['row']
            fig.add_shape(dict(
                type="rect", line={"width": 1, "dash": "dot", "color": "darkgrey"},
                xref=f"x{dvars.index(row) + 1}", yref=f"y{dvars.index(row) + 1}",
                **info['bounds'],
            ))

    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=10),
        yaxis=dict(tickfont=dict(size=20)),
        legend=dict(x=1.09, bordercolor='#d3d3d3', borderwidth=1, bgcolor='white',
                    font=dict(size=14), traceorder='normal',
                    title=dict(text=' ovar', font=dict(size=14))),
        barmode="stack",
        annotations=[
            dict(x=1.09, y=1.0 - (i - 0.5) / len(dvars), xref="paper", yref="paper",
                 text=dvar, showarrow=False, xanchor="right", yanchor="middle",
                 font=dict(size=14), textangle=90)
            for i, dvar in enumerate(dvars, 1)
        ],
        showlegend=True, selectdirection='h', dragmode='select',
    )
    return fig
