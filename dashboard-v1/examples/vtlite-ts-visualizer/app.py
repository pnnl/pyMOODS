import dash
from dash import dcc, html, Input, Output, callback_context
import pandas as pd
import plotly.graph_objects as go

# Load dataset
df = pd.read_csv('./public/scenarios.csv')

# Get list of numeric columns for plotting, excluding 'sim' and 'time'
numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
for col in ['sim', 'time']:
    if col in numeric_cols:
        numeric_cols.remove(col)

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Scenario Time Series Viewer"

# App layout
app.layout = html.Div([
    html.H1("Time Series Dashboard for Scenario Data", style={'textAlign': 'center'}),

    html.Div([
        html.Label("Select Case Study:"),
        dcc.Dropdown(
            id='case-study-dropdown',
            options=[{'label': cs, 'value': cs} for cs in df['Case Study'].unique()],
            value=df['Case Study'].iloc[0]
        )
    ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),

    html.Div([
        html.Label("Select Location:"),
        dcc.Dropdown(
            id='location-dropdown',
            options=[{'label': loc, 'value': loc} for loc in df['Location'].unique()],
            value=df['Location'].iloc[0]
        )
    ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),

    html.Div([
        html.Label("Select Variable(s):"),
        dcc.Dropdown(
            id='variable-dropdown',
            options=[{'label': v, 'value': v} for v in numeric_cols],
            value=numeric_cols[0],
            multi=True
        )
    ], style={'width': '60%', 'padding': '10px'}),

    dcc.Graph(id='time-series-plot')
])


# Helper function to filter data based on dropdowns
def get_filtered_df(case_study, location):
    return df[(df['Case Study'] == case_study) & (df['Location'] == location)]


# Main Graph Update Callback
@app.callback(
    Output('time-series-plot', 'figure'),
    [
        Input('case-study-dropdown', 'value'),
        Input('location-dropdown', 'value'),
        Input('variable-dropdown', 'value')
    ]
)
def update_graph(case_study, location, variables):
    if not isinstance(variables, list):
        variables = [variables]

    filtered_df = get_filtered_df(case_study, location)

    fig = go.Figure()

    # Define a consistent color palette
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    var_color_map = {var: colors[i % len(colors)] for i, var in enumerate(variables)}

    for var in variables:
        color = var_color_map[var]
        for sim_id, grouped_df in filtered_df.groupby('sim'):
            fig.add_trace(go.Scatter(
                x=grouped_df['time'],
                y=grouped_df[var],
                mode='lines',
                name=f"{var} - Sim {sim_id}",
                hoverinfo='name+x+y',
                customdata=[[var, sim_id]] * len(grouped_df),
                line=dict(color=color, width=1.5),
                opacity=0.4,
                showlegend=False
            ))

    fig.update_layout(
        title=f"Time Series for {case_study} in {location}",
        xaxis_title="Time",
        yaxis_title="Value",
        hovermode='closest',
        template='plotly_white',
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='lightgray'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='lightgray'),
        margin=dict(l=50, r=50, t=50, b=50),
        font=dict(family="Arial", size=12, color="#333"),
        transition_duration=500
    )

    return fig


# Highlight on Hover Callback
@app.callback(
    Output('time-series-plot', 'figure', allow_duplicate=True),
    Input('time-series-plot', 'hoverData'),
    Input('case-study-dropdown', 'value'),
    Input('location-dropdown', 'value'),
    Input('variable-dropdown', 'value'),
    prevent_initial_call=True
)
def highlight_on_hover(hover_data, case_study, location, variables):
    if not hover_data or not variables:
        return dash.no_update

    try:
        highlighted_var = hover_data['points'][0]['customdata'][0]
        highlighted_sim = hover_data['points'][0]['customdata'][1]
    except (KeyError, IndexError):
        return dash.no_update

    filtered_df = get_filtered_df(case_study, location)
    fig = go.Figure()

    # Reuse same color map logic
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    var_color_map = {var: colors[i % len(colors)] for i, var in enumerate(variables)}

    for var in variables:
        color = var_color_map[var]
        for sim_id, grouped_df in filtered_df.groupby('sim'):
            if var == highlighted_var and sim_id == highlighted_sim:
                fig.add_trace(go.Scatter(
                    x=grouped_df['time'],
                    y=grouped_df[var],
                    mode='lines',
                    name=f"{var} - Sim {sim_id}",
                    hoverinfo='name+x+y',
                    customdata=[[var, sim_id]] * len(grouped_df),
                    line=dict(color=color, width=3),
                    opacity=1,
                    showlegend=False
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=grouped_df['time'],
                    y=grouped_df[var],
                    mode='lines',
                    name=f"{var} - Sim {sim_id}",
                    hoverinfo='name+x+y',
                    customdata=[[var, sim_id]] * len(grouped_df),
                    line=dict(color='gray'),
                    opacity=0.15,  # further greyed out
                    showlegend=False
                ))

    fig.update_layout(
        title=f"Time Series for {case_study} in {location}",
        xaxis_title="Time",
        yaxis_title="Value",
        hovermode='closest',
        template='plotly_white',
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='lightgray'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='lightgray'),
        margin=dict(l=50, r=50, t=50, b=50),
        font=dict(family="Arial", size=12, color="#333"),
        transition_duration=500
    )

    return fig


if __name__ == '__main__':
    app.run(debug=True)