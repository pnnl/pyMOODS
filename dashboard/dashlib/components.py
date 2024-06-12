import pandas as pd
import plotly.graph_objs as go
import numpy as np


def blank_figure():
    fig = go.Figure(go.Scatter(x=[], y=[]))
    fig.update_layout(template=None)
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False)

    return fig


def gen_graph(df):
    fig = go.Figure()
    if ('tab-1-example-graph') and df is not None and isinstance(
            df, pd.DataFrame):
        f_cols = [col for col in df.columns if col.startswith('f') or col.startswith('o')]
        num_objective_functions = len(f_cols)

        if num_objective_functions >= 2:
            if num_objective_functions == 2:
                x_column, y_column = f_cols[:2]
                fig.add_trace(
                    go.Scattergl(
                        x=df[x_column],
                        y=df[y_column],
                        # hovertemplate='(x = %{x}, y= %{y})<extra></extra>',
                        mode="markers",
                        marker=dict(color='rgba(0,0,0,0)',
                                    size=18,
                                    line=dict(color='mediumpurple',
                                              width=2)),
                        hoverlabel=dict(font_size=18),
                        # selected=go.scatter.Selected(marker={
                        #     'size': 40,
                        #     "color": "LightSeaGreen"
                        # })
                    ))
                fig.update_traces(
                 hovertemplate='f1: %{x}<br>f2: %{y}<extra></extra>', hoverlabel=dict(font_size=18))
                fig.update_layout(
                    dragmode='select',
                    xaxis=dict(title='f1',
                               showgrid=True,
                               showline=True,
                               zeroline=False,
                               linewidth=2,
                               linecolor='black',
                               title_font=dict(size=18),
                               title_standoff=5,
                               automargin=True),
                    yaxis=dict(title='f2',
                               showgrid=True,
                               zeroline=False,
                               showline=True,
                               linewidth=2,
                               linecolor='black',
                               title_font=dict(size=18),
                               title_standoff=5,
                               automargin=True),
                    font=dict(color="black", size=18),
                    clickmode='event+select',
                    mapbox={
                        'style': "stamen-terrain",
                        'zoom': 6
                    },
                    hovermode='closest',
                    # font_color='black',
                    # template=None,
                    font_family="Helvetica",
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor='rgb(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                )
            else:
                df = df.T
                f_colss = [col for col in df.index if col.startswith('f')]

                for col in f_colss:
                    fig.add_vline(x=col,
                                  line_width=3,
                                  line_dash="dash",
                                  line_color="green")
                for col in df.columns:
                    fig.add_trace(
                        go.Scatter(x=df.index.values[df.index.str.startswith('f')],
                                   y=df[col][df.index.str.startswith('f')],
                                   mode='lines+markers',
                                   name=str(col),
                                   line=dict(color='Mediumpurple')
                                   ))

                fig.update_layout(
                    showlegend=False,
                    dragmode='select',
                    xaxis=dict(
                        tickmode='array',
                        tickvals=np.arange(len(df)),
                        ticktext=[col for col in f_colss],
                        automargin=True,
                        title_font=dict(size=18)
                    ),
                    # yaxis=dict(title='Values'),
                    # clickmode='event+select',
                    hovermode='closest',
                    paper_bgcolor='rgb(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="black", size=18),
                    margin=dict(l=20, r=20, t=30, b=10),
                )
#                 if num_objective_functions == 2:


                # elif num_objective_functions == 3:
#                 else:
#                     fig.add_trace(
#                         go.Scatter3d(
#                             x=df[f_cols[0]],
#                             y=df[f_cols[1]],
#                             z=df[f_cols[2]],
#                             hovertemplate=
#                             'f1: %{x}<br>f2: %{y}<br>f3: %{z}<extra></extra>',
#                             mode="markers",
#                             marker=dict(size=15,
#                                         line=dict(color='MediumPurple',
#                                                   width=2),
#                                         symbol='circle'),
#                         ))
#                     fig.update_layout(scene=dict(xaxis=dict(title='f1', title_font=dict(size=18), backgroundcolor='rgba(0,0,0,0)',
#                                         showline= True, showgrid=True, zeroline=False, linewidth=2,linecolor='black', zerolinecolor="black"),
#                                                  yaxis=dict(title='f2', title_font=dict(size=18), backgroundcolor='rgba(0,0,0,0)',
#                                         showline= True,showgrid=True, zeroline=False, linewidth=2,linecolor='black', zerolinecolor="black"),
#                                                  zaxis=dict(title='f3', title_font=dict(size=18), backgroundcolor='rgba(0,0,0,0)',
#                                          showline= True,showgrid=True, zeroline=False, linewidth=2,linecolor='black', zerolinecolor="black")),
#                                       clickmode='event+select',
#                                       hovermode='closest',
#                                       font_family="Helvetica",
#                                       margin=dict(l=0, r=0, t=0, b=28),
#                                       paper_bgcolor='rgb(0,0,0,0)',
#                                       plot_bgcolor='rgba(0,0,0,0)')


         

    else:
        print("Invalid data format")
    return fig
