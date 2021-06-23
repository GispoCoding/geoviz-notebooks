import sys
import csv
import geopandas as gpd
import osmnx as ox
import pandana
from ipygis import get_connection_url
from shapely.geometry import Point
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoResultFound
from geoalchemy2.shape import from_shape

# test simple import now, convert to module later
sys.path.insert(0, "..")
from models import OSMAccessNode

sql_url = get_connection_url(dbname="geoviz")
engine = create_engine(sql_url)
session = sessionmaker(bind=engine)()
OSMAccessNode.__table__.create(engine, checkfirst=True)

# Select city (COP, HEL, WAR)
city = 'HEL'

if city == 'COP':
    cityname = 'Copenhagen, Denmark'
    minx, miny, maxx, maxy = 12.42000, 55.61000, 12.65000, 55.78000
elif city == 'HEL':
    cityname = 'Helsinki, Finland'
    minx, miny, maxx, maxy = 24.82345, 60.14084, 25.06404, 60.29496
elif city == 'WAR':
    cityname = 'Warsaw, Poland'
    minx, miny, maxx, maxy = 20.79057, 52.09901, 21.31300, 52.38502

print(f"Fetching graph for {city} from overpass API...")
# Get graph by geocoding
try:
    graph = ox.graph_from_place(cityname, network_type="walk")
    ignore_geocoding = False
# Get graph based on bbox if geocoding fails (copenhagen has no polygon on nominatim)
except ValueError:
    graph = ox.graph_from_bbox(maxy, miny, maxx, minx, network_type="walk")
    ignore_geocoding = True

print("Projecting graph...")
# Project graph for accurate simplification (and more accurate poi centroids later on)
graph = ox.projection.project_graph(graph, to_crs=3035)
points_to_add = {}

# Simplify graph (try to get real intersections only)
# Will lose lots of intersections atm!
# graph = ox.simplification.consolidate_intersections(
#     # Graph to simplify
#     graph,
#     # consolidate nodes within 10m from eachother
#     tolerance=10,
#     # Get result as graph (False to get nodes only as gdf)
#     rebuild_graph=True,
#     # Include dead ends
#     dead_ends=True,
#     # Reconnect the graph
#     reconnect_edges=True
# )

# Max time to walk in minutes (no routing to nodes further than this)
walk_time = 15
# Walking speed
walk_speed = 4.5
# Set a uniform walking speed on every edge
for u, v, data in graph.edges(data=True):
    data['speed_kph'] = walk_speed

graph = ox.add_edge_travel_times(graph)

print("Extracting geodataframes...")
# Extract node/edge GeoDataFrames, retaining only necessary columns (for pandana)
nodes = ox.graph_to_gdfs(graph, edges=False)[['x', 'y']]
edges = ox.graph_to_gdfs(graph, nodes=False).reset_index()[['u', 'v', 'travel_time']]

# Select pois based on osm tags
tags = {
    'amenity':[
        'cafe',
        'bar',
        'pub',
        'restaurant'
    ],
    'shop':[
        'bakery',
        'convenience',
        'supermarket',
        'mall',
        'department_store',
        'clothes',
        'fashion',
        'shoes'
    ],
    'leisure':[
        'fitness_centre'
    ]
}

print("Constructing amenities POIs...")
# Get amentities from place/bbox
if ignore_geocoding is True:
    amenities = ox.geometries.geometries_from_bbox(
        maxy, miny, maxx, minx,
        tags=tags
    )
else:
    amenities = ox.geometries.geometries_from_place(
        cityname,
        tags=tags
    )
# Project amenities
amenities = amenities.to_crs(epsg=3035)
# Construct the pandana network model
network = pandana.Network(
    node_x=nodes['x'],
    node_y=nodes['y'], 
    edge_from=edges['u'],
    edge_to=edges['v'],
    edge_weights=edges[['travel_time']]
)
# Extract centroids from the amenities' geometries
centroids = amenities.centroid
# Specify a max travel distance for analysis
# Minutes -> seconds
maxdist = walk_time * 60
# Set the amenities' locations on the network
network.set_pois(
    category='pois',
    maxdist=maxdist,
    maxitems=10,
    x_col=centroids.x, 
    y_col=centroids.y
)

print("Calculating distances to amenities...")
# calculate travel time to 10 nearest amenities from each node in network
distances = network.nearest_pois(
    distance=maxdist,
    category='pois',
    num_pois=10
)

# Get simplified nodes with wgs coords
graph_wgs = ox.projection.project_graph(graph, to_crs=4326)
nodes_wgs = ox.graph_to_gdfs(graph_wgs, edges=False)[['x', 'y']]# Join travel time info to nodes
walk_access = nodes.join(distances, on='osmid', how='left')
walk_access_wgs = nodes_wgs.join(distances, on='osmid', how='left')
walk_access_dict = walk_access_wgs.to_dict(orient='index')
nodes_to_save = {}
print(walk_access_dict)
print(f"Found {len(walk_access_dict)} accessibility nodes, importing...")
for key, value in walk_access_dict.items():
    node_id = key
    geom = from_shape(Point(float(value.pop("x")), float(value.pop("y"))), srid=4326)
    # use dict, since the json may contain the same stop twice!
    if node_id in nodes_to_save:
        print(f"Node {node_id} found twice, overwriting")
    nodes_to_save[node_id] = OSMAccessNode(node_id=node_id, accessibilities=value, geom=geom)
print(f"Saving {len(nodes_to_save)} accessibility nodes...")
session.bulk_save_objects(nodes_to_save.values())
session.commit()
