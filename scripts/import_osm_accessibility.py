import argparse
import logging
from logging import Logger
import sys
import osmnx as ox
import pandana
from ipygis import get_connection_url
from shapely.geometry import Point
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List
from geoalchemy2.shape import from_shape
from slugify import slugify

# test simple import now, convert to module later
sys.path.insert(0, "..")
from models import OSMAccessNode
from osm_tags import tags_to_filter


class AccessibilityImporter(object):
    def __init__(self, slug: str, bbox: List[float], logger: Logger):
        if not slug:
            raise AssertionError("You must specify the city name.")
        (self.minx, self.miny, self.maxx, self.maxy) = bbox
        self.logger = logger

        sql_url = get_connection_url(dbname="geoviz")
        engine = create_engine(sql_url)
        schema_engine = engine.execution_options(
            schema_translate_map={'schema': slug}
        )
        self.session = sessionmaker(bind=schema_engine)()
        OSMAccessNode.__table__.drop(schema_engine, checkfirst=True)
        OSMAccessNode.__table__.create(schema_engine)

    def run(self):
        self.logger.info("Fetching graph from Overpass API...")
        # Get graph based on bbox
        graph = ox.graph_from_bbox(
            self.maxy, self.miny, self.maxx, self.minx, network_type="walk"
        )

        self.logger.info("Projecting graph...")
        # Project graph for accurate simplification (and more accurate poi centroids later on)
        graph = ox.projection.project_graph(graph, to_crs=3035)

        # Max time to walk in minutes (no routing to nodes further than this)
        walk_time = 15
        walk_speed = 4.5
        # Set a uniform walking speed on every edge
        for u, v, data in graph.edges(data=True):
            data["speed_kph"] = walk_speed

        graph = ox.add_edge_travel_times(graph)

        self.logger.info("Extracting geodataframes...")
        # Extract node/edge GeoDataFrames, retaining only necessary columns (for pandana)
        nodes = ox.graph_to_gdfs(graph, edges=False)[["x", "y"]]
        edges = ox.graph_to_gdfs(graph, nodes=False).reset_index()[
            ["u", "v", "travel_time"]
        ]

        # Select pois based on osm tags
        self.logger.info("Constructing amenities POIs...")
        # Get amentities from place/bbox
        amenities = ox.geometries.geometries_from_bbox(
            self.maxy, self.miny, self.maxx, self.minx, tags=tags_to_filter
        )
        # Project amenities
        amenities = amenities.to_crs(epsg=3035)
        # Construct the pandana network model
        network = pandana.Network(
            node_x=nodes["x"],
            node_y=nodes["y"],
            edge_from=edges["u"],
            edge_to=edges["v"],
            edge_weights=edges[["travel_time"]],
        )
        # Extract centroids from the amenities' geometries
        centroids = amenities.centroid
        # Specify a max travel distance for analysis
        # Minutes -> seconds
        maxdist = walk_time * 60
        # 1 minute max distance from POIs to network
        mapping_distance = 60

        # Set the amenities' locations on the network
        network.set_pois(
            category="pois",
            maxdist=maxdist,
            maxitems=10,
            mapping_distance=mapping_distance,
            x_col=centroids.x,
            y_col=centroids.y,
        )

        self.logger.info("Calculating distances to amenities...")
        # calculate travel time to 10 nearest amenities from each node in network
        distances = network.nearest_pois(distance=maxdist, category="pois", num_pois=10)

        # Get simplified nodes with wgs coords
        graph_wgs = ox.projection.project_graph(graph, to_crs=4326)
        nodes_wgs = ox.graph_to_gdfs(graph_wgs, edges=False)[
            ["x", "y"]
        ]  # Join travel time info to nodes
        walk_access_wgs = nodes_wgs.join(distances, on="osmid", how="left")
        walk_access_dict = walk_access_wgs.to_dict(orient="index")
        nodes_to_save = {}
        self.logger.info(f"Found {len(walk_access_dict)} accessibility nodes, importing...")
        for key, value in walk_access_dict.items():
            node_id = key
            geom = from_shape(
                Point(float(value.pop("x")), float(value.pop("y"))), srid=4326
            )
            # use dict, since the json may contain the same stop twice!
            if node_id in nodes_to_save:
                self.logger.info(f"Node {node_id} found twice, overwriting")
            nodes_to_save[node_id] = OSMAccessNode(
                node_id=node_id, accessibilities=value, geom=geom
            )
        self.logger.info(f"Saving {len(nodes_to_save)} accessibility nodes...")
        self.session.bulk_save_objects(nodes_to_save.values())
        self.session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Do OSM accessibility analysis for given boundingbox"
    )
    parser.add_argument("-bbox", default=None, help="Bounding box of area to import")
    parser.add_argument("-city", default="HEL", help="City to import")
    args = vars(parser.parse_args())
    arg_slug = slugify(args["city"])
    arg_bbox = args["bbox"]
    arg_bbox = list(map(float, arg_bbox.split(", ")))
    importer = AccessibilityImporter(arg_slug, arg_bbox, logging.getLogger("import"))

    importer.run()
