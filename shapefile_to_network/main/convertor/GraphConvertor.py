import fiona
import geopy.distance
import networkx as nx
from haversine import haversine
from shapely.geometry import shape
from shapely.ops import unary_union

class GraphConvertor:
    def __init__(self, input_file, output_dir):
        self.input_file = input_file
        self.output_dir = output_dir

    '''
        @input:     The path of the shapefile which need to be converted to network
        @output:    Returns the MultiDigraph created from the shapefile

        This function read the shapefile of the road network and convert it into graph by iterating through the lat, lon
        from the shapefile.
    '''

    def shape_convertor(self):
        geoms = [shape(feature['geometry']) for feature in fiona.open(self.input_file)]
        res = unary_union(geoms)
        G = nx.MultiDiGraph()
        for line in res:
            for seg_start, seg_end in zip(list(line.coords), list(line.coords)[1:]):
                start = (round(seg_start[1], 6), round(seg_start[0], 6))
                end = (round(seg_end[1], 6), round(seg_end[0], 6))
                G.add_edge(start, end, weight=haversine(start, end))
        return G

    '''
        @input:     The Graph and the path

        This function read the Graph, iterate over the list of nodes in the graph and save it into file defined by path
    '''

    def create_vertex_file(self, g):
        vertex = g.nodes
        output = open(self.output_dir + '/vertex.csv', 'w')
        output.write('Unique Id; Longitude; Latitude\n')

        count = 1
        for v in vertex:
            output.write(str(count) + ';' + str(round(v[0], 6)) + ';' + str(round(v[1], 6)) + '\n')
            count += 1

    '''
        @input:     The Graph and directory

        This function writes the graph in form of shape file to the given directory
    '''

    def create_edges_vertex_shape(self, g):
        nx.write_shp(g, self.output_dir + '/New Shape/')

    '''
        @input:     The Graph and the path

        This function iterate over the edges of the graph and write it into the file defined by the path
    '''

    def create_edges_file(self, g):
        output = open(self.output_dir + '/edges.csv', 'w')
        output.write('Starting Coordinate; End Coordinate; True Distance(km) \n')

        for edge in g.edges:
            distance = g.get_edge_data(edge[0], edge[1])[0]['weight']
            start_coor = [round(elem, 6) for elem in list(edge[0])]
            end_coor = [round(elem, 6) for elem in list(edge[1])]
            output.write(str(start_coor) + ';' + str(end_coor) + ';' + str(distance) + '\n')

    '''
        @input:     path of the shape file and the output for saving clean network
        @output:    Cleaned network

        This function read the input shape file and convert it into network for cleaning. After converting it simplify the
        graph by calling simplify_graph() and write the cleaned network in form of shapefiles
    '''

    def graph_convertor(self):
        G = self.shape_convertor()
        nodes = G.nodes()
        #print("Number of Nodes in the graph, ", len(nodes))

        #Add new edges over pacific
        for node in nodes:
            if node[1] > 170:
                for node2 in nodes:
                    if node2[1] < -170:
                        if (node[0] - 10) < node2[0] < (node[0] + 10):
                            distance = geopy.distance.distance(node, node2)
                            G.add_edge(node, node2, weight=distance.km)

        #Add new nodes and edges for Spain
        G.add_node((44.52736554981609, -3.6442414724703953))
        G.add_node((46.35277724558476, -3.762119252196382))

        for node in nodes:
            if -2 > node[1] > -5:
                if 48 > node[0] > 42:
                    for node2 in nodes:
                        if -2 > node2[1] > -5:
                            if 48 > node2[0] > 42:
                                distance = geopy.distance.distance(node, node2)
                                G.add_edge(node, node2, weight=distance.km)

        #simplify_graph = GraphSimplify(G)
        #new_G = simplify_graph.simplify_graph()

        #print("Number of Nodes after simplifying, ", len(new_G.nodes))
        #self.create_vertex_file(new_G)
        #self.create_edges_file(new_G)

        #multiDi_to_simple = MultiDiToSimple(new_G)
        #new_simple_graph = multiDi_to_simple.convert_MultiDi_to_Simple()
        #self.create_edges_vertex_shape(new_simple_graph)

        return G
