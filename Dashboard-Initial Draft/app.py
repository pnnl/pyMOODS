from matplotlib import figure
import pandas as pd
from dash import Dash, dcc, html
import plotly.express as px
import plotly.graph_objs as go
import plotly.io as pio
from dash.dependencies import Input, Output
import seaborn as sns
import dash_bootstrap_components as dbc

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

df1 = pd.read_csv("/Users/matt412/Downloads/2V-2O (1).csv")
df2 = pd.read_csv("/Users/matt412/Downloads/2V-4O (1).csv")
df3 = pd.read_csv("/Users/matt412/Downloads/4V-2O (1).csv")
df4 = pd.read_csv("/Users/matt412/Downloads/4V-4O (1).csv")


app.layout = html.Div(
    [
        html.H1(
            children="MOO Visualization",
            style={
                "font-family": "Gill Sans",
                "font-weight": "medium",
                "text-align": "center",
            },
        ),
        dcc.Dropdown(
            id="my_dropdown",
            options=[
                {
                    "label": "2 Variables - 2 Objective Functions",
                    "value": "/Users/matt412/Downloads/2V-2O (1).csv",
                },
                {
                    "label": "2 Variables - 4 Objective Functions",
                    "value": "/Users/matt412/Downloads/2V-4O (1).csv",
                },
                {
                    "label": "4 Variables - 2 Objective Functions",
                    "value": "/Users/matt412/Downloads/4V-2O (1).csv",
                },
                {
                    "label": "4 Variables - 4 Objective Functions",
                    "value": "/Users/matt412/Downloads/4V-4O (1).csv",
                },
            ],
            value="/Users/matt412/Downloads/2V-2O (1).csv",
            optionHeight=25,
            multi=False,
            searchable=True,
            style={"width": "100%", "font-family": "Gill Sans", "top": "0"},
        ),
        html.Div(
            [
                dbc.Row(
            [
                dbc.Col(html.H5("Objective Space"), style={"width": "50%", "textAlign":"center","fontWeight" : "bold","textDecoration" : "underline","justify": "between","padding":"2rem"}),
                dbc.Col(html.H5("Decision Space"), style={"width": "50%", "textAlign":"center","fontWeight" : "bold","textDecoration" : "underline","justify": "between","padding":"2rem"}),
            ]
        ),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(dcc.Graph(id="fig1")),
                            style={"width": "50%", "justify": "between", "tilteText":"tt"},
                        ),
                        dbc.Col(
                            html.Div(dcc.Graph(id="fig2")),
                            style={"width": "50%", "justify": "between"},
                        ),
                    ]
                ),
                #dbc.Row(
                #    [
                #        dbc.Col(
                #            html.Div(dcc.Graph(id="fig3")),
                #            style={"width": "50%", "justify": "between"},
                #        ),
                #        dbc.Col(
                #            html.Div(dcc.Graph(id="fig4")),
                #            style={"width": "50%", "justify": "between"},
                #        ),
                #    ]
                #),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(dcc.Graph(id="fig5")),
                            style={"width": "50%", "justify": "between"},
                        ),
                        dbc.Col(
                            html.Div(dcc.Graph(id="fig6")),
                            style={"width": "50%", "justify": "between"},
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(dcc.Graph(id="fig7")),
                            style={"width": "50%", "justify": "between"},
                        ),
                        dbc.Col(
                            html.Div(dcc.Graph(id="fig8")),
                            style={"width": "50%", "justify": "between"},
                        ),
                    ]
                ),
                #dbc.Row(
                #    [
                #        dbc.Col(
                #            html.Div(dcc.Graph(id="fig9")),
                #            style={"width": "50%", "justify": "between"},
                #        ),
                #        dbc.Col(
                #            html.Div(dcc.Graph(id="fig10")),
                #            style={"width": "50%", "justify": "between"},
                #        ),
                #    ]
                #)
            ]
        ),
    ]
)


@app.callback(
    Output("fig1", "figure"),
    Output("fig2", "figure"),
    #Output("fig3", "figure"),
    #Output("fig4", "figure"),
    Output("fig5", "figure"),
    Output("fig6", "figure"),
    Output("fig7", "figure"),
    Output("fig8", "figure"),
    #Output("fig9", "figure"),
    #Output("fig10", "figure"),
    [Input("my_dropdown", "value")],
)
def update_output(my_dropdown):
    if my_dropdown == "/Users/matt412/Downloads/2V-2O (1).csv":
        scatter = px.scatter(
            df1,
            x=df1["f1"],
            y=df1["f2"],
            labels={"df1[f1]": "f1", "df1[f2]": "f2"},
            title="Scatter Plot",
        )
        scatter_d = px.scatter(
            df1,
            x=df1["x1"],
            y=df1["x2"],
            labels={"df1[x1]": "x1", "df1[x2]": "x2"},
            title="Scatter Plot",
        )

        # bubble = go.Figure(
        #     data=go.Scatter(
        #         x=df1["f1"],
        #         y=df1["f2"],
        #         mode="markers",
        #         marker_size=df1["f1"]+df1["f2"],
        #     )
        # )
        # bubble_d = go.Figure(
        #     data=go.Scatter(
        #         x=df1["x1"],
        #         y=df1["x2"],
        #         mode="markers",
        #         marker_size=df1["x1"]+df1["x2"],
        #         #[0, 20, 40, 60, 80, 100, 120],
        #     )
        #)

        parallel = px.parallel_coordinates(
            df1,
            dimensions=["f1", "f2"],
            labels={"df1[f1]": "f1", "df1[f2]": "f2"},
            title="Parallel Coordinates",
        )
        parallel_d = px.parallel_coordinates(
            df1,
            dimensions=["x1", "x2"],
            labels={"df1[x1]": "x1", "df1[x2]": "x2"},
            title="Parallel Coordinates",
        )

        data1 = df1[["f1", "f2"]].values.tolist()
        heatmap = px.imshow(
            data1,
            labels={"df1[f1]": "f1", "df1[f2]": "f2"},
            x=["f1", "f2"],
            color_continuous_scale=px.colors.sequential.Pinkyl,
            title="Heatmap",
        )
        data2 = df1[["x1", "x2"]].values.tolist()
        heatmap_d = px.imshow(
            data2,
            labels={"df1[x1]": "x1", "df1[x2]": "x2"},
            x=["x1", "x2"],
            color_continuous_scale=px.colors.sequential.Pinkyl,
            title="Heatmap",
        )
        
        # polar = go.Figure()
        # polar.add_trace(go.Scatterpolar(
        #     r = df1["x1"],
        #     theta = df1["f1"],
        #     mode = 'lines',
        #     line_color='peru'
        # ))
        # polar.add_trace(go.Scatterpolar(
        #     r = df1["x1"],
        #     theta = df1["f2"],
        #     mode = 'lines',
        #     line_color='darkviolet'
        # ))
        # polar.add_trace(go.Scatterpolar(
        #     r = df1["x2"],
        #     theta = df1["f1"],
        #     mode = 'lines',
        #     line_color='black'
        # ))
        # polar.add_trace(go.Scatterpolar(
        #     r = df1["x2"],
        #     theta = df1["f2"],
        #     mode = 'lines',
        #     line_color='deepskyblue'
        # ))
        
        #polar = px.scatter_polar(df1, r = ["x1", "x2"], theta= ["f1","f2"] )
        
        # polar_data = pd.melt(df1,id_vars=["x1","x2"], var_name="Objective functions", value_vars=['f1','f2'],)
        # print(polar_data)
        # polar = px.line_polar(polar_data, r ='value', theta ='Objective functions', color = "x2", line_close= True, line_shape = 'spline', markers=True,color_discrete_sequence=px.colors.sequential.Plasma_r,
        #             template="plotly_dark",)
        #polar_fig = px.line_polar(polar)

        return scatter, scatter_d, parallel, parallel_d, heatmap, heatmap_d

    elif my_dropdown == "/Users/matt412/Downloads/2V-4O (1).csv":
        scatter = px.scatter_3d(
            df2,
            x=df2["f1"],
            y=df2["f2"],
            z=df2["f3"],
            color=df2["f4"],
            labels={"df2[f1]": "f1", "df2[f2]": "f2", "df2[f3]": "f3", "df2[f4]": "f4"},
            title="Scatter Plot",
        )
        scatter_d = px.scatter(
            df2,
            x=df2["x1"],
            y=df2["x2"],
            labels={"df2[x1]": "x1", "df2[x2]": "x2"},
            title="Scatter Plot",
        )

        # bubble = px.scatter_3d(
        #     x=df2["f1"],
        #     y=df2["f2"],
        #     z=df2["f3"],
        #     color=df2["f4"],
        #     size_max=300,
        #     title="Bubble Chart",
        # )
        # bubble_d = go.Figure(
        #     data=go.Scatter(
        #         x=df2["x1"],
        #         y=df2["x2"],
        #         mode="markers",
        #         marker_size=[0, 20, 40, 60, 80, 100, 120],
        #     )
        # )

        parallel = px.parallel_coordinates(
            df2,
            dimensions=["f1", "f2", "f3", "f4"],
            labels={"df2[f1]": "f1", "df2[f2]": "f2", "df2[f3]": "f3", "df2[f4]": "f4"},
            title="Parallel Coordinates",
        )
        parallel_d = px.parallel_coordinates(
            df2,
            dimensions=["x1", "x2"],
            labels={"df2[x1]": "x1", "df2[x2]": "x2"},
            title="Parallel Coordinates",
        )

        data3 = df2[["f1", "f2", "f3", "f4"]].values.tolist()
        heatmap = px.imshow(
            data3,
            labels={"df2[f1]": "f1", "df2[f2]": "f2", "df2[f3]": "f3", "df2[f4]": "f4"},
            x=["f1", "f2", "f3", "f4"],
            color_continuous_scale=px.colors.sequential.Pinkyl,
            title="Heatmap",
        )
        data4 = df2[["x1", "x2"]].values.tolist()
        heatmap_d = px.imshow(
            data4,
            labels={"df2[x1]": "x1", "df2[x2]": "x2"},
            x=["x1", "x2"],
            color_continuous_scale=px.colors.sequential.Pinkyl,
            title="Heatmap",
        )

        return scatter, scatter_d, parallel, parallel_d, heatmap, heatmap_d

    elif my_dropdown == "/Users/matt412/Downloads/4V-2O (1).csv":
        scatter = px.scatter(
            df3,
            x=df3["f1"],
            y=df3["f2"],
            labels={"df3[f1]": "f1", "df3[f2]": "f2"},
            title="Scatter Plot",
        )
        scatter_d = px.scatter_3d(
            df3,
            x=df3["x1"],
            y=df3["x2"],
            z=df3["x3"],
            color=df3["x4"],
            labels={"df3[x1]": "x1", "df3[x2]": "x2", "df3[x3]": "x3", "df3[x4]": "x4"},
            title="Scatter Plot",
        )

        # bubble = go.Figure(
        #     data=go.Scatter(
        #         x=df3["f1"],
        #         y=df3["f2"],
        #         mode="markers",
        #         marker_size=[0, 20, 40, 60, 80, 100, 120],
        #     )
        # )
        # bubble_d = px.scatter_3d(
        #     x=df3["x1"],
        #     y=df3["x2"],
        #     z=df3["x3"],
        #     color=df3["x4"],
        #     size_max=300,
        #     title="Bubble Chart",
        # )

        parallel = px.parallel_coordinates(
            df3,
            dimensions=["f1", "f2"],
            labels={"df3[f1]": "f1", "df3[f2]": "f2"},
            title="Parallel Coordinates",
        )
        parallel_d = px.parallel_coordinates(
            df3,
            dimensions=["x1", "x2", "x3", "x4"],
            labels={"df3[x1]": "x1", "df3[x2]": "x2", "df3[x3]": "x3", "df3[x4]": "x4"},
            title="Parallel Coordinates",
        )

        data5 = df3[["f1", "f2"]].values.tolist()
        heatmap = px.imshow(
            data5,
            labels={"df3[f1]": "f1", "df3[f2]": "f2"},
            x=["f1", "f2"],
            color_continuous_scale=px.colors.sequential.Pinkyl,
            title="Heatmap",
        )
        data6 = df3[["x1", "x2", "x3", "x4"]].values.tolist()
        heatmap_d = px.imshow(
            data6,
            labels={"df3[x1]": "x1", "df3[x2]": "x2", "df3[x3]": "x3", "df3[x4]": "x4"},
            x=["x1", "x2", "x3", "x4"],
            color_continuous_scale=px.colors.sequential.Pinkyl,
            title="Heatmap",
        )
        return scatter, scatter_d, parallel, parallel_d, heatmap, heatmap_d

    elif my_dropdown == "/Users/matt412/Downloads/4V-4O (1).csv":
        scatter = px.scatter_3d(
            df4,
            x=df4["f1"],
            y=df4["f2"],
            z=df4["f3"],
            color=df4["f4"],
            labels={"df4[f1]": "f1", "df4[f2]": "f2", "df4[f3]": "f3", "df4[f4]": "f4"},
            title="Scatter Plot",
        )
        scatter_d = px.scatter_3d(
            df4,
            x=df4["x1"],
            y=df4["x2"],
            z=df4["x3"],
            color=df4["x4"],
            labels={"df4[x1]": "x1", "df4[x2]": "x2", "df4[x3]": "x3", "df4[x4]": "x4"},
            title="Scatter Plot",
        )

        # bubble = px.scatter_3d(
        #     df4,
        #     x=df4["f1"],
        #     y=df4["f2"],
        #     z=df4["f3"],
        #     color=df4["f4"],
        #     size_max=40,
        #     labels={"df4[f1]": "f1", "df4[f2]": "f2", "df4[f3]": "f3", "df4[f4]": "f4"},
        #     title=" Bubble Chart",
        # )
        # bubble_d = px.scatter_3d(
        #     df4,
        #     x=df4["x1"],
        #     y=df4["x2"],
        #     z=df4["x3"],
        #     color=df4["x4"],
        #     size_max=40,
        #     labels={"df4[x1]": "x1", "df4[x2]": "x2", "df4[x3]": "x3", "df4[x4]": "x4"},
        #     title=" Bubble Chart",
        # )

        parallel = px.parallel_coordinates(
            df4,
            dimensions=["f1", "f2", "f3", "f4"],
            labels={"df4[f1]": "f1", "df4[f2]": "f2", "df4[f3]": "f3", "df4[f4]": "f4"},
            title="Parallel Coordinates",
        )
        parallel_d = px.parallel_coordinates(
            df4,
            dimensions=["x1", "x2", "x3", "x4"],
            labels={"df4[x1]": "x1", "df4[x2]": "x2", "df4[x3]": "x3", "df4[x4]": "x4"},
            title="Parallel Coordinates",
        )

        data7 = df4[["f1", "f2", "f3", "f4"]].values.tolist()
        heatmap = px.imshow(
            data7,
            labels={"df4[f1]": "f1", "df4[f2]": "f2", "df4[f3]": "f3", "df4[f4]": "f4"},
            x=["f1", "f2", "f3", "f4"],
            color_continuous_scale=px.colors.sequential.Pinkyl,
            title="Heatmap",
        )
        data8 = df4[["x1", "x2", "x3", "x4"]].values.tolist()
        heatmap_d = px.imshow(
            data8,
            labels={"df4[x1]": "x1", "df4[x2]": "x2", "df4[x3]": "x3", "df4[x4]": "x4"},
            x=["x1", "x2", "x3", "x4"],
            color_continuous_scale=px.colors.sequential.Pinkyl,
            title="Heatmap",
        )

        return scatter, scatter_d, parallel, parallel_d, heatmap, heatmap_d


if __name__ == "__main__":
    app.run_server(debug=True)
