import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def plot_maps(df):
    """Plots maps showing various cost metrics for producing H2."""

    df = pd.read_csv('Results/final_df.csv', index_col=0)

    fig = go.Figure(data=go.Scattergeo(
        lat=df.loc[:, 'Latitude'],
        lon=df.loc[:, 'Longitude'],
        mode='markers',
        marker=dict(
            color=df.loc[:, 'Total Cost per kg H2'],
            size=2,
        ),
    ))

    fig.update_layout(
        geo=dict(
            showland=True,
            landcolor="rgb(212, 212, 212)",
            subunitcolor="rgb(255, 255, 255)",
            countrycolor="rgb(255, 255, 255)",
            showlakes=True,
            lakecolor="rgb(255, 255, 255)",
            showsubunits=True,
            showcountries=True,
            projection=dict(
                type='natural earth'
            ),
        ),
        title='Total cost per kg H2 (Eur)'
    )
    fig.show()

    return
