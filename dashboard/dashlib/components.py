import pandas as pd
import plotly.graph_objs as go

def blank_figure():
    fig = go.Figure(go.Scatter(x=[], y=[]))
    fig.update_layout(template=None)
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False)

    return fig

def gen_graph(df, tab):
    fig = go.Figure()
    if (tab == 'tab-1-example-graph') and df is not None:
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
                    mode="markers",
                    marker={
                        'size': 10,
                        "color": "blue"
                    },
                    selected=go.scatter.Selected(marker={
                        'size': 25,
                        "color": "LightSeaGreen"
                    })))
        else:
            print("Invalid data format")
            return fig

        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        fig.update_layout(
            font=dict(color="black", size=22, family="Courier New"),
            clickmode='event+select',
            mapbox={
                'style': "stamen-terrain",
                'zoom': 6
            },
            hovermode='closest',
            xaxis_title='f1',
            yaxis_title='f2',
            font_color='black',
            font_family="Courier New",
            margin=dict(l=10, r=20, t=20, b=0),
            # title="Objective Space",
            paper_bgcolor='rgb(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
    return fig