from mc_geo_path import *
from generation_costs import *
from mc_parameter_def import *

def mc_main(end_plant_tuple, h2_demand, year=2019, centralised=True, pipeline=True, max_pipeline_dist=2000, iterations=1000):
    """Runs a monte carlo simulation of the model. Takes the desired end location [lat, long], the H2 demand (
    kt/yr), the year, if redistribution is centralised or not, if pipelines are allowed, and the maximum allowed
    pipeline distance (km) as input. Calculates the minimum of (transport + generation) cost for all possible start
    locations to determine the cheapest source of renewable H2. """

    df = pd.read_csv('Data/renewables.csv', index_col=0)

    # Define parameters for generation costs
    capex_extra, capex_h2, lifetime_hours, electrolyser_efficiency, elec_opex, other_capex_elec, water_cost, \
    capex_wind, opex_wind, capex_solar, opex_factor_solar = define_gen_parameters(year, iterations)

    initial_geo_calcs(df, end_plant_tuple, iterations=iterations, centralised=centralised, pipeline=pipeline, max_pipeline_dist=max_pipeline_dist)

