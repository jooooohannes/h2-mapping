import pandas as pd
from Transport_cost_functions import *
from geo_path import *
import plotly.graph_objects as go

def print_basic_results(df):
    """Prints the important results from the input dataframe."""

    min_cost = min(df['Total Cost per kg H2'])
    mindex = df.index.values[df['Total Cost per kg H2'] == min_cost]
    mindex = mindex[0]
    cheapest_source = (df['Latitude'][mindex], df['Longitude'][mindex])
    cheapest_medium = df['Cheapest Medium'][mindex]
    cheapest_elec = df['Cheaper source'][mindex]

    print('Index: ' + str(mindex))
    print('Minimum cost: ' + str(min_cost))
    print('Cheapest source: ' + str(cheapest_source[0]) + ', ' + str(cheapest_source[1]))
    print('Cheapest medium: ' + str(cheapest_medium))
    print('Cheaper electricity: ' + str(cheapest_elec))

    return min_cost, mindex


def get_path(df, end_plant_tuple, centralised, pipeline):
    """Prints and plots the path of transport taken from the cheapest found solution."""

    min_cost = min(df['Total Cost per kg H2'])
    mindex = df.index.values[df['Total Cost per kg H2'] == min_cost]
    mindex = mindex[0]

    df, end_port_tuple = check_port_path(df, end_plant_tuple)

    # Get straight line distance from end point to end port
    direct_distance_end = geopy.distance.distance(end_plant_tuple, end_port_tuple).km  # Needs [lat, long]
    try:
        driving_distance_end = get_driving_distance(end_plant_tuple, end_port_tuple)  # Needs [lat, long]
    except:
        driving_distance_end = np.nan

    # Calculate minimum costs from end port to end location for all medium possibilities
    end_nh3_options = [nh3_costs(truck_dist=driving_distance_end, convert=False, centralised=centralised),
                       nh3_costs(pipe_dist=direct_distance_end, convert=False, centralised=centralised, pipeline=pipeline),
                       h2_gas_costs(pipe_dist=direct_distance_end, pipeline=pipeline),
                       h2_gas_costs(truck_dist=driving_distance_end)]
    cost_end_nh3 = np.nanmin(end_nh3_options)
    try:
        end_nh3_transport = end_nh3_options.index(np.nanmin(end_nh3_options))
        if end_nh3_transport == 0:
            nh3_end = 'NH3 Truck'
        elif end_nh3_transport == 1:
            nh3_end = 'NH3 Pipe'
        elif end_nh3_transport == 2:
            nh3_end = 'H2 Gas Pipe'
        elif end_nh3_transport == 3:
            nh3_end = 'H2 Gas Truck'
    except:
        nh3_end = 'Not possible'
    end_lohc_options = [lohc_costs(truck_dist=driving_distance_end, convert=False, centralised=centralised),
                        h2_gas_costs(pipe_dist=direct_distance_end, pipeline=pipeline),
                        h2_gas_costs(truck_dist=driving_distance_end)]
    cost_end_lohc = np.nanmin(end_lohc_options)
    try:
        end_lohc_transport = end_lohc_options.index(np.nanmin(end_lohc_options))
        if end_lohc_transport == 0:
            lohc_end = 'LOHC Truck'
        elif end_lohc_transport == 1:
            lohc_end = 'H2 Gas Pipe'
        elif end_lohc_transport == 2:
            lohc_end = 'H2 Gas Truck'
    except:
        lohc_end = 'Not possible'
    end_h2_liq_options = [h2_liq_costs(truck_dist=driving_distance_end, convert=False, centralised=centralised),
                          h2_gas_costs(pipe_dist=direct_distance_end, pipeline=pipeline),
                          h2_gas_costs(truck_dist=driving_distance_end)]
    cost_end_h2_liq = np.nanmin(end_h2_liq_options)
    try:
        end_h2_liq_transport = end_h2_liq_options.index(np.nanmin(end_h2_liq_options))
        if end_h2_liq_transport == 0:
            h2_liq_end = 'H2 Liq Truck'
        elif end_h2_liq_transport == 1:
            h2_liq_end = 'H2 Gas Pipe'
        elif end_h2_liq_transport == 2:
            h2_liq_end = 'H2 Gas Truck'
    except:
        h2_liq_end = 'Not possible'

    direct_distance_total = geopy.distance.distance((df.at[mindex, 'Latitude'], df.at[mindex, 'Longitude']),
                                                    end_plant_tuple).km  # Needs [lat, long]

    # Check if it is possible to truck the whole way to end destination. If so, get costs.
    if direct_distance_total < 500:
        try:
            driving_distance_total = get_driving_distance((df.at[mindex, 'Latitude'], df.at[mindex, 'Longitude']),
                                                          end_plant_tuple)  # Needs [lat, long]
        except:
            driving_distance_total = np.nan
    else:
        driving_distance_total = np.nan

    # Calculate minimum costs from gen to start port for all medium possibilities
    start_nh3_options = [
        nh3_costs(truck_dist=df.at[mindex, 'Gen-Port Driving Dist.'], convert=False, centralised=centralised),
        nh3_costs(pipe_dist=df.at[mindex, 'Gen-Port Direct Dist.'], convert=False, centralised=centralised, pipeline=pipeline),
        h2_gas_costs(pipe_dist=df.at[mindex, 'Gen-Port Direct Dist.'], pipeline=pipeline),
        h2_gas_costs(truck_dist=df.at[mindex, 'Gen-Port Driving Dist.'])]
    cost_start_nh3 = np.nanmin(start_nh3_options)
    start_nh3_transport = start_nh3_options.index(np.nanmin(start_nh3_options))
    if start_nh3_transport == 0:
        nh3_start = 'NH3 Truck'
    elif start_nh3_transport == 1:
        nh3_start = 'NH3 Pipe'
    elif start_nh3_transport == 2:
        nh3_start = 'H2 Gas Pipe'
    elif start_nh3_transport == 3:
        nh3_start = 'H2 Gas Truck'
    start_lohc_options = [
        lohc_costs(truck_dist=df.at[mindex, 'Gen-Port Driving Dist.'], convert=False, centralised=centralised),
        h2_gas_costs(pipe_dist=df.at[mindex, 'Gen-Port Direct Dist.'], pipeline=pipeline),
        h2_gas_costs(truck_dist=df.at[mindex, 'Gen-Port Driving Dist.'])]
    cost_start_lohc = np.nanmin(start_lohc_options)
    start_lohc_transport = start_lohc_options.index(np.nanmin(start_lohc_options))
    if start_lohc_transport == 0:
        lohc_start = 'LOHC Truck'
    elif start_lohc_transport == 1:
        lohc_start = 'H2 Gas Pipe'
    elif start_lohc_transport == 2:
        lohc_start = 'H2 Gas Truck'
    start_h2_liq_options = [
        h2_liq_costs(truck_dist=df.at[mindex, 'Gen-Port Driving Dist.'], convert=False, centralised=centralised),
        h2_gas_costs(pipe_dist=df.at[mindex, 'Gen-Port Direct Dist.'], pipeline=pipeline),
        h2_gas_costs(truck_dist=df.at[mindex, 'Gen-Port Driving Dist.'])]
    cost_start_h2_liq = np.nanmin(start_h2_liq_options)
    start_h2_liq_transport = start_h2_liq_options.index(np.nanmin(start_h2_liq_options))
    if start_h2_liq_transport == 0:
        h2_liq_start = 'H2 Liq Truck'
    elif start_h2_liq_transport == 1:
        h2_liq_start = 'H2 Gas Pipe'
    elif start_h2_liq_transport == 2:
        h2_liq_start = 'H2 Gas Truck'

    # Calculate shipping costs
    cost_shipping_nh3 = nh3_costs(ship_dist=df['Shipping Dist.'][mindex], centralised=centralised)
    cost_shipping_lohc = lohc_costs(ship_dist=df['Shipping Dist.'][mindex], centralised=centralised)
    cost_shipping_h2_liq = h2_liq_costs(ship_dist=df['Shipping Dist.'][mindex], centralised=centralised)

    # Calculate minimum total transport costs for each medium
    total_nh3_options = [(cost_start_nh3 + cost_shipping_nh3 + cost_end_nh3),
                         nh3_costs(truck_dist=driving_distance_total, centralised=centralised),
                         nh3_costs(pipe_dist=direct_distance_total, centralised=centralised, pipeline=pipeline)]
    nh3_options = total_nh3_options.index(np.nanmin(total_nh3_options))
    if nh3_options == 0:
        nh3 = 'NH3 Ship'
    elif nh3_options == 1:
        nh3 = 'NH3 Truck'
    elif nh3_options == 2:
        nh3 = 'NH3 Pipe'
    total_lohc_options = [(cost_start_lohc + cost_shipping_lohc + cost_end_lohc),
                          lohc_costs(truck_dist=driving_distance_total, centralised=centralised)]
    lohc_options = total_lohc_options.index(np.nanmin(total_lohc_options))
    if lohc_options == 0:
        lohc = 'LOHC Ship'
    elif lohc_options == 1:
        lohc = 'LOHC Truck'
    total_h2_liq_options = [(cost_start_h2_liq + cost_shipping_h2_liq + cost_end_h2_liq),
                            h2_liq_costs(truck_dist=driving_distance_total, centralised=centralised)]
    h2_liq_options = total_h2_liq_options.index(np.nanmin(total_h2_liq_options))
    if h2_liq_options == 0:
        h2_liq = 'H2 Liq Ship'
    elif h2_liq_options == 1:
        h2_liq = 'H2 Liq Truck'
    total_h2_gas_options = [h2_gas_costs(truck_dist=driving_distance_total),
                            h2_gas_costs(pipe_dist=direct_distance_total, pipeline=pipeline)]
    try:
        h2_gas_options = total_h2_gas_options.index(np.nanmin(total_h2_gas_options))
        if h2_gas_options == 0:
            h2_gas = 'H2 Gas Truck'
        elif h2_gas_options == 1:
            h2_gas = 'H2 Gas Pipe'
    except:
        h2_gas = 'Not possible'

    total_total_options = [df.at[mindex, 'NH3 Cost'], df.at[mindex, 'LOHC Cost'], df.at[mindex, 'H2 Liq Cost'],
                           df.at[mindex, 'H2 Gas Cost']]
    if np.nanmin(total_total_options) == df.at[mindex, 'NH3 Cost']:
        if nh3 == 'NH3 Ship':
            final_path = nh3_start + ' + Ship + ' + nh3_end
        else:
            final_path = nh3
    elif np.nanmin(total_total_options) == df.at[mindex, 'LOHC Cost']:
        if lohc == 'LOHC Ship':
            final_path = lohc_start + ' + Ship + ' + lohc_end
        else:
            final_path = lohc
    elif np.nanmin(total_total_options) == df.at[mindex, 'H2 Liq Cost']:
        if h2_liq == 'H2 Liq Ship':
            final_path = h2_liq_start + ' + Ship + ' + h2_liq_end
        else:
            final_path = h2_liq
    elif np.nanmin(total_total_options) == df.at[mindex, 'H2 Gas Cost']:
        final_path = h2_gas

    print('Transport method: ' + final_path)

    return final_path





