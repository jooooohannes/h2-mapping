import pandas as pd
import numpy as np
from geo_path import *
from generation_costs import *
from print_results import *
from plot_results import *
import timeit


def main(end_tuple, h2_demand, year=2020, centralised=True, pipeline=True, max_pipeline_dist=2000):
    """Executes a single run of the complete model. Takes the desired end location [lat, long], the H2 demand (
    kt/yr), the year, if redistribution is centralised or not, if pipelines are allowed, and the maximum allowed
    pipeline distance (km) as input. Calculates the minimum of (transport + generation) cost for all possible start
    locations to determine the cheapest source of renewable H2. """

    df = pd.read_csv('Data/renewables.csv', index_col=0)

    # Calculate generation and transport costs
    print('Calculating generation costs...')
    df = generation_costs(df, h2_demand, year=year)
    print('Calculating transport costs...')
    df = transport_costs(df, end_tuple, h2_demand, centralised=centralised, pipeline=pipeline, max_pipeline_dist=max_pipeline_dist)

    df['Total Yearly Cost'] = df['Yearly gen. cost'] + df['Yearly Transport Cost']
    df['Total Cost per kg H2'] = df['Gen. cost per kg H2'] + df['Transport Cost per kg H2']

    df.to_csv('Results/' + str(round(end_tuple[0])) + ',' + str(round(end_tuple[1])) + '.csv')

    return df

# Define parameters for the main model
end_tuple = (25.28893697992723, 51.565533460963046)   # [lat, long]
h2_demand = 50  # [kt/yr]
year = 2020
centralised = True
pipeline = True
max_pipeline_dist = 2000

# start timer
start = timeit.default_timer()

df = main(end_tuple, h2_demand, year, centralised, pipeline, max_pipeline_dist)

df.to_csv('Results/final_df.csv')

# stop timer
stop = timeit.default_timer()
print('Total Time: ', stop - start)

print_basic_results(df)

get_path(df, end_tuple, centralised, pipeline)
