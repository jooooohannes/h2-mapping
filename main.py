import pandas as pd
import numpy as np
from geo_path import *
from generation_costs import *
from results import *
import timeit


def main(end_tuple, h2_demand, year=2019, centralised=True):
    """Executes a single run of the complete model. Takes the desired end location [lat, long] and the H2 demand (
    kt/yr) as input. Calculates the minimum of (transport + generation) cost for all possible start locations to
    determine the cheapest source of renewable H2. """

    df = pd.read_csv('Data/renewables.csv', index_col=0)

    # Calculate generation and transport costs
    print('Calculating generation costs...')
    df = generation_costs(df, h2_demand, year=year)
    print('Calculating transport costs...')
    df = transport_costs(df, end_tuple, h2_demand, centralised=centralised)

    df['Total Yearly Cost'] = df['Yearly gen. cost'] + df['Yearly Transport Cost']
    df['Total Cost per kg H2'] = df['Gen. cost per kg H2'] + df['Transport Cost per kg H2']

    return df

# Define parameters for the main model
end_tuple = (54.1036450555351, 7.646171232141434)  # [lat, long]
h2_demand = 50  # [kt/yr]
year = 2019
centralised = True

# start timer
start = timeit.default_timer()

df = main(end_tuple, h2_demand, year, centralised)

df.to_csv('Results/final_df.csv')

# stop timer
stop = timeit.default_timer()
print('Total Time: ', stop - start)

print_basic_results(df)

get_path(df, end_tuple, centralised)

