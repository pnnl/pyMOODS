import pandas as pd
import plotly.graph_objs as go


def blank_figure():
    fig = go.Figure(go.Scatter(x=[], y=[]))
    fig.update_layout(template=None)
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False)

    return fig


def gen_graph(df):
    fig = go.Figure()
    if ('tab-1-example-graph') and df is not None:
        if isinstance(df, pd.DataFrame):
            f_cols = [col for col in df.columns if col.startswith('f')]
            if len(f_cols) >= 2:
                x_column, y_column = f_cols[:2]
            else:
                print("Error: Insufficient columns starting with 'f'")
                return fig
            fig.add_trace(
                go.Scatter(
                    x=df[x_column],
                    y=df[y_column],
                    hovertemplate='<b>f1</b>: %{x}' +
                    '<br><b>f2</b>: %{y}<extra></extra>',
                    # hoverinfo='text',
                    # text=f'f1: {df[0]: .2f}<br>f2: {df[1]: .2f}',
                    hoverlabel=dict(font_size=22),
                    mode="markers",
                    marker=dict(color='rgba(0,0,0,0)',
                                size=20,
                                line=dict(color='MediumPurple', width=2)),
                    selected=go.scatter.Selected(marker={
                        'size': 40,
                        "color": "LightSeaGreen"
                    })))
        else:
            print("Invalid data format")
            return fig

        fig.update_xaxes(showgrid=False,
                         showline=True,
                         zeroline=False,
                         linewidth=2,
                         linecolor='black',
                         title_font=dict(size=50),
                         title_standoff=5,
                         automargin=True)
        fig.update_yaxes(
            showgrid=False,
            zeroline=False,
            showline=True,
            linewidth=2,
            linecolor='black',
            #  tickwidth=17,
            title_font=dict(size=50),
            title_standoff=5,
            automargin=True)
        fig.update_layout(
            font=dict(color="black", size=22),
            clickmode='event+select',
            mapbox={
                'style': "stamen-terrain",
                'zoom': 6
            },
            hovermode='closest',
            xaxis_title='f1',
            yaxis_title='f2',
            font_color='black',
            template=None,
            font_family="Helvetica",
            margin=dict(l=10, r=20, t=20, b=0),
            # title="Objective Space",
            paper_bgcolor='rgb(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
    return fig
