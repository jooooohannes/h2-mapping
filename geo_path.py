import pandas as pd
from scipy import spatial
import sys
import numpy as np
import geopy.distance
import requests
import timeit
import json
from Transport_cost_functions import *

sys.path.append("C:/Users/Jason Collis/Documents/Papers/mapping paper/model/shapefile_to_network/main/convertor")
sys.path.append("C:/Users/Jason Collis/Documents/Papers/mapping paper/model/shapefile_to_network/main/shortest_paths")

from shapefile_to_network.main.convertor.GraphSimplify import GraphSimplify
from shapefile_to_network.main.convertor.GraphConvertor import GraphConvertor
from shapefile_to_network.main.shortest_paths.ShortestPath import ShortestPath, closest_node
from shapefile_to_network.main.metrics.Centrality import Centrality
from shapely import speedups

speedups.disable()


def get_driving_distance(start_point, end_point):
    """Gets the driving distance (km) from the start point to the end point (input in [lat, long])."""

    # call the OSMR API - needs [long, lat]
    r = requests.get(
        f"http://router.project-osrm.org/route/v1/car/{end_point[1]},{end_point[0]};{start_point[1]},{start_point[0]}?overview=false""")
    # then you load the response using the json libray
    # by default you get only one alternative so you access 0-th element of the `routes`
    routes = json.loads(r.content)
    route_1 = routes.get("routes")[0]
    driving_distance = route_1["distance"] / 1000

    return driving_distance


def create_port_coordinates(df_ports):
    """Creates a list of the port co-ordinates that can be used to find the nearest port to any point. Requires no
    input."""

    coords = df_ports['coords'].values.tolist()
    coords = [i.strip('()') for i in coords]
    coords = [i.strip("'),'") for i in coords]
    coords = [i.split(', ') for i in coords]

    coords2 = []
    for i in range(len(coords)):
        li = []
        for j in range(2):
            li.append(float(coords[i][j]))
        coords2.append(li)

    return coords2


def create_network():
    """Converts the shapefile of shipping routes downloaded online into a network using GraphConvertor.py. Requires
    no input. """

    # Create GraphConvertor object by passing the path of input shapefile and the output directory
    input_file = 'Data/shipping/shipping_routes/shipping_routes.shp'
    output_dir = 'Data/shipping/nodes'

    graph_convertor_obj = GraphConvertor(input_file, output_dir)

    # Call graph_convertor function to convert the input shapefile into road network and save the newly created
    # shapefile into specifed output_dir along with list of nodes and edges in .csv files
    network = graph_convertor_obj.graph_convertor()

    return network


def shipping_distance(shortest_path_obj, start_tuple, end_tuple):
    """ Finds the shortest shipping route between a singular start and end point using the Dijkstra algorithm
    provided by Networkx. Requires as input the shortest_path object as well as start and end points (lat, long)."""

    # Find number of shortest paths from origin to destination in new simplified network
    try:
        shortest_paths, buffered_graph = shortest_path_obj.find_shortest_paths(start_tuple, end_tuple)
        shortest_dis = min(shortest_paths.keys())
    except:
        shortest_dis = None
        print('No path found between ' + str(start_tuple) + ' and ' + str(end_tuple))

    return shortest_dis


def create_shipping_path(df, end_port_tuple):
    """Creates a path between all the starting ports and the end port. Takes about 15-20 minutes. Requires as input the main
    dataframe containing port longitude and latitude and the desired end port location (lat, long)."""

    g = create_network()

    alpha = 0.1
    graph_buffer = 300
    point_buffer = 1
    break_point = 1  # Upper limit to save computation time

    # Create ShortestPath object by passing all required parameters
    shortest_path_obj = ShortestPath(g, alpha, graph_buffer, point_buffer, break_point)
    df['Shipping Dist.'] = np.zeros(len(df))

    for i in range(len(df)):
        if i == 1000 or i == 2000 or i == 3000 or i == 4000 or i == 5000:
            print('Iterations complete: ' + str(i) + '/' + str(len(df)))
        if df.at[i, 'Shipping Dist.'] == 0:
            end_plant_tuple = (df.at[i, 'Port Lat.'], df.at[i, 'Port Long.'])
            df.at[i, 'Shipping Dist.'] = shipping_distance(shortest_path_obj, end_plant_tuple,
                                                           end_port_tuple)

            for j in range(len(df)):
                if df.at[i, 'Port Code'] == df.at[j, 'Port Code']:
                    df.at[j, 'Shipping Dist.'] = df.at[i, 'Shipping Dist.']

    return df


def check_port_path(df, end_plant_tuple):
    """Checks if the paths to the end port have already been calculated. If they have, finds the appropriate data from
    the port index dataframe. If not, calculates it using the function create_path, which takes around 15 minutes.
    Takes as input the main dataframe, the end point (lat, lon) and a list of all the port co-ordinates."""

    df_port_index = pd.read_csv('Data/port_index.csv', index_col=0)
    df_ports = pd.read_csv('Data/path/ports.csv')

    port_coords = create_port_coordinates(df_ports)

    end_plant_tuple = end_plant_tuple[::-1]

    # Find the closest port to the end point
    distance, index = spatial.KDTree(port_coords).query(end_plant_tuple)  # Needs [long, lat]
    end_port_code = df_ports.at[index, 'Unnamed: 0']
    print('End Port Code: ' + str(end_port_code))
    end_port_tuple = port_coords[index][::-1]  # Outputs [long, lat]

    # Check if port code is in the port distances index. If not, create new shipping paths and add them to the index.
    try:
        df['Shipping Dist.'] = df_port_index[str(end_port_code)]
    except:
        print('Creating new shipping distances (should take 15-20 mins)...')
        df = create_shipping_path(df, end_port_tuple)
        df_port_index[end_port_code] = df['Shipping Dist.']
        df_port_index.to_csv('Data/port_index.csv')

    return df, end_port_tuple


def transport_costs(df, end_plant_tuple, h2_demand, centralised=True, pipeline=True, max_pipeline_dist=2000):
    """Calculates the transport costs from all start points to the end point. Takes in the main dataframe,
    the end point tuple (lat, lon) and if the distribution point is centralised or not as input. Adds in shipping
    distances from start port to end port and driving and direct distances from end port to consumption point.
    Calculates costs for all transport media for both land and sea journeys, as well as for all transport media. For
    land journeys, both direct pipeline and trucking is considered. """

    df, end_port_tuple = check_port_path(df, end_plant_tuple)

    # Get straight line distance from end point to end port
    direct_distance_end = geopy.distance.distance(end_plant_tuple, end_port_tuple).km  # Needs [lat, long]
    try:
        driving_distance_end = get_driving_distance(end_plant_tuple, end_port_tuple)  # Needs [lat, long]
    except:
        driving_distance_end = np.nan

    # Calculate minimum costs from end port to end location for all medium possibilities
    end_nh3_options = [nh3_costs(truck_dist=driving_distance_end, convert=False, centralised=centralised),
                       nh3_costs(pipe_dist=direct_distance_end, convert=False, centralised=centralised, pipeline=pipeline, max_pipeline_dist=max_pipeline_dist),
                       h2_gas_costs(pipe_dist=direct_distance_end, pipeline=pipeline, max_pipeline_dist=max_pipeline_dist),
                       h2_gas_costs(truck_dist=driving_distance_end)]
    cost_end_nh3 = np.nanmin(end_nh3_options)
    end_lohc_options = [lohc_costs(truck_dist=driving_distance_end, convert=False, centralised=centralised),
                        h2_gas_costs(pipe_dist=direct_distance_end, pipeline=pipeline, max_pipeline_dist=max_pipeline_dist),
                        h2_gas_costs(truck_dist=driving_distance_end)]
    cost_end_lohc = np.nanmin(end_lohc_options)
    end_h2_liq_options = [h2_liq_costs(truck_dist=driving_distance_end, convert=False, centralised=centralised),
                          h2_gas_costs(pipe_dist=direct_distance_end, pipeline=pipeline, max_pipeline_dist=max_pipeline_dist),
                          h2_gas_costs(truck_dist=driving_distance_end)]
    cost_end_h2_liq = np.nanmin(end_h2_liq_options)

    df['NH3 Cost'] = np.zeros(len(df))
    df['LOHC Cost'] = np.zeros(len(df))
    df['H2 Liq Cost'] = np.zeros(len(df))
    df['H2 Gas Cost'] = np.zeros(len(df))
    df['Transport Cost per kg H2'] = np.zeros(len(df))
    df['Cheapest Medium'] = np.zeros(len(df))
    df['Direct Dist.'] = np.zeros(len(df))
    df['Driving Dist.'] = np.zeros(len(df))

    print('Starting final transport calculations...')

    for i in range(len(df)):
        if i == 1000 or i == 2000 or i == 3000 or i == 4000 or i == 5000:
            print('Iterations complete: ' + str(i) + '/' + str(len(df)))
        direct_distance_total = geopy.distance.distance((df.at[i, 'Latitude'], df.at[i, 'Longitude']),
                                                        end_plant_tuple).km  # Needs [lat, long]

        # Check if it is possible to truck the whole way to end destination. If so, get costs.
        if direct_distance_total < 700:
            try:
                driving_distance_total = get_driving_distance((df.at[i, 'Latitude'], df.at[i, 'Longitude']),
                                                              end_plant_tuple)  # Needs [lat, long]
            except:
                driving_distance_total = np.nan
        else:
            driving_distance_total = np.nan

        df.at[i, 'Direct Dist.'] = direct_distance_total
        df.at[i, 'Driving Dist.'] = driving_distance_total

        # Calculate minimum costs from gen to start port for all medium possibilities
        start_nh3_options = [
            nh3_costs(truck_dist=df.at[i, 'Gen-Port Driving Dist.'], convert=False, centralised=centralised),
            nh3_costs(pipe_dist=df.at[i, 'Gen-Port Direct Dist.'], convert=False, centralised=centralised, pipeline=pipeline, max_pipeline_dist=max_pipeline_dist),
            h2_gas_costs(pipe_dist=df.at[i, 'Gen-Port Direct Dist.'], pipeline=pipeline, max_pipeline_dist=max_pipeline_dist),
            h2_gas_costs(truck_dist=df.at[i, 'Gen-Port Driving Dist.'])]
        cost_start_nh3 = np.nanmin(start_nh3_options)
        start_lohc_options = [
            lohc_costs(truck_dist=df.at[i, 'Gen-Port Driving Dist.'], convert=False, centralised=centralised),
            h2_gas_costs(pipe_dist=df.at[i, 'Gen-Port Direct Dist.'], pipeline=pipeline, max_pipeline_dist=max_pipeline_dist),
            h2_gas_costs(truck_dist=df.at[i, 'Gen-Port Driving Dist.'])]
        cost_start_lohc = np.nanmin(start_lohc_options)
        start_h2_liq_options = [
            h2_liq_costs(truck_dist=df.at[i, 'Gen-Port Driving Dist.'], convert=False, centralised=centralised),
            h2_gas_costs(pipe_dist=df.at[i, 'Gen-Port Direct Dist.'], pipeline=pipeline, max_pipeline_dist=max_pipeline_dist),
            h2_gas_costs(truck_dist=df.at[i, 'Gen-Port Driving Dist.'])]
        cost_start_h2_liq = np.nanmin(start_h2_liq_options)

        # Calculate shipping costs
        cost_shipping_nh3 = nh3_costs(ship_dist=df.at[i, 'Shipping Dist.'], centralised=centralised)
        cost_shipping_lohc = lohc_costs(ship_dist=df.at[i, 'Shipping Dist.'], centralised=centralised)
        cost_shipping_h2_liq = h2_liq_costs(ship_dist=df.at[i, 'Shipping Dist.'], centralised=centralised)

        # Calculate minimum total transport costs for each medium
        total_nh3_options = [(cost_start_nh3 + cost_shipping_nh3 + cost_end_nh3),
                             nh3_costs(truck_dist=driving_distance_total, centralised=centralised),
                             nh3_costs(pipe_dist=direct_distance_total, centralised=centralised, pipeline=pipeline, max_pipeline_dist=max_pipeline_dist)]
        df.at[i, 'NH3 Cost'] = np.nanmin(total_nh3_options)
        total_lohc_options = [(cost_start_lohc + cost_shipping_lohc + cost_end_lohc),
                              lohc_costs(truck_dist=driving_distance_total, centralised=centralised)]
        df.at[i, 'LOHC Cost'] = np.nanmin(total_lohc_options)
        total_h2_liq_options = [(cost_start_h2_liq + cost_shipping_h2_liq + cost_end_h2_liq),
                                h2_liq_costs(truck_dist=driving_distance_total, centralised=centralised)]
        df.at[i, 'H2 Liq Cost'] = np.nanmin(total_h2_liq_options)
        total_h2_gas_options = [h2_gas_costs(truck_dist=driving_distance_total),
                                h2_gas_costs(pipe_dist=direct_distance_total, pipeline=pipeline, max_pipeline_dist=max_pipeline_dist)]
        df.at[i, 'H2 Gas Cost'] = np.nanmin(total_h2_gas_options)

        total_total_options = [df.at[i, 'NH3 Cost'], df.at[i, 'LOHC Cost'], df.at[i, 'H2 Liq Cost'],
                               df.at[i, 'H2 Gas Cost']]
        df.at[i, 'Transport Cost per kg H2'] = np.nanmin(total_total_options)

        # Get overall cheapest medium and therefore lowest transport costs
        transport_costs_dict = {'NH3': df.at[i, 'NH3 Cost'], 'LOHC': df.at[i, 'LOHC Cost'],
                                'H2 Liq': df.at[i, 'H2 Liq Cost'],
                                'H2 Gas': df.at[i, 'H2 Gas Cost']}
        df.loc[i, 'Cheapest Medium'] = min(transport_costs_dict, key=transport_costs_dict.get)

    df['Yearly Transport Cost'] = df['Transport Cost per kg H2'] * (h2_demand * 1000 * 1000)

    return df
