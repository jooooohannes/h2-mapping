from mc_geo_path import *
from mc_generation_costs import *
from mc_parameter_def import *
import timeit
import os


def mc_main(end_plant_tuple, h2_demand, year=2021, centralised=True, pipeline=True, max_pipeline_dist=2000,
            iterations=1000, elec_type='Alkaline'):
    """Runs a monte carlo simulation of the model. Takes the desired end location [lat, long], the H2 demand (
    kt/yr), the year, if redistribution is centralised or not, if pipelines are allowed, and the maximum allowed
    pipeline distance (km) as input. Calculates the minimum of (transport + generation) cost for all possible start
    locations to determine the cheapest source of renewable H2. """

    df = pd.read_csv('Data/renewables.csv', index_col=0)

    total_cost_per_kg_h2 = np.zeros((iterations, len(df)))
    generation_cost_per_kg = np.zeros((iterations, len(df)))
    solar_cost = np.zeros((iterations, len(df)))
    wind_cost = np.zeros((iterations, len(df)))

    # Define parameters for generation costs
    year_diff, capex_extra, capex_h2, lifetime_hours, electrolyser_efficiency, elec_opex, other_capex_elec, water_cost, \
    capex_wind, opex_wind, capex_solar, opex_factor_solar = define_gen_parameters(year, iterations, elec_type)

    df, cost_end_nh3, cost_end_lohc, cost_end_h2_liq = initial_geo_calcs(df, end_plant_tuple,
                                                                         centralised=centralised, pipeline=pipeline,
                                                                         max_pipeline_dist=max_pipeline_dist)

    for i in range(iterations):
        df = mc_generation_costs(df, h2_demand, year_diff, capex_extra[i], capex_h2[i], lifetime_hours,
                                 electrolyser_efficiency[i], elec_opex[i],
                                 other_capex_elec[i], water_cost[i],
                                 capex_wind[i], opex_wind[i], capex_solar[i], opex_factor_solar[i],
                                 interest=0.08, full_load_hours=2000)

        df = mc_transport_costs(df, end_plant_tuple, h2_demand, cost_end_nh3, cost_end_lohc, cost_end_h2_liq,
                                centralised=centralised, pipeline=pipeline,
                                max_pipeline_dist=max_pipeline_dist)

        df['Total Yearly Cost'] = df['Yearly gen. cost'] + df['Yearly Transport Cost']
        df['Total Cost per kg H2'] = df['Gen. cost per kg H2'] + df['Transport Cost per kg H2']

        total_cost_per_kg_h2[i, :] = df['Total Cost per kg H2'].values
        generation_cost_per_kg[i, :] = df['Gen. cost per kg H2'].values
        solar_cost[i, :] = df['Elec Cost Solar'].values
        wind_cost[i, :] = df['Elec Cost Wind'].values

    return total_cost_per_kg_h2, generation_cost_per_kg, solar_cost, wind_cost


# Define parameters for the main model
end_tuple = [(23.0550, 113.4242), (29.6084, -95.0527)]  # [lat, long]
h2_demand = [100]  # [kt/yr]
year = [2030]
centralised = True
pipeline = True
max_pipeline_dist = 10000
iterations = 1000
elec_type = ['alkaline']

for et in end_tuple:
    print('Location: ' + str(et))
    for h2 in h2_demand:
        print('H2 Demand: ' + str(h2))
        for yr in year:
            print('Year: ' + str(yr))
            for elec in elec_type:
                print('Elec type: ' + elec)

                # start timer
                start = timeit.default_timer()

                total_cost_per_kg_h2, generation_cost_per_kg_h2, solar_cost, wind_cost = mc_main(et, h2, yr, centralised, pipeline, max_pipeline_dist, iterations, elec)

                newpath = "Results/mc/" + str(round(et[0])) + ',' + str(round(et[1])) + '__' + str(yr) + '__' + str(h2) + '__' + elec + '__' + str(pipeline) + '__' + str(iterations)
                if pipeline == True:
                    newpath = newpath + '__Pipe'
                if centralised == False:
                    newpath = newpath + '__decent'

                if not os.path.exists(newpath):
                    os.makedirs(newpath)

                np.savetxt(newpath + '/' + 'total_cost_per_kg_h2.csv', total_cost_per_kg_h2, delimiter=",")
                np.savetxt(newpath + '/' + 'generation_cost_per_kg_h2.csv', generation_cost_per_kg_h2, delimiter=",")
                np.savetxt(newpath + '/' + 'solar_cost.csv', solar_cost, delimiter=",")
                np.savetxt(newpath + '/' + 'wind_cost.csv', wind_cost, delimiter=",")

                # stop timer
                stop = timeit.default_timer()
                print('Total Time: ', stop - start)
