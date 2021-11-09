import argparse
import sys
import osmnx as ox
from ipygis import get_connection_url
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.schema import CreateSchema
from geoalchemy2 import Geometry, WKTElement
from typing import Dict

# test simple import now, convert to module later
sys.path.insert(0, "..")
from models import OSMPoint
from osm_tags import tags_to_filter


class OsmImporter(object):
    """Import OSM data to PostGIS using Overpass API."""

    def __init__(self, args: Dict):
        args = self._parse_args(args)
        self.slug = args["slug"]
        self.bbox = args["bbox"]
        self.city = args["city_name"]
        self._engine = self._create_engine()

    @staticmethod
    def _parse_args(args) -> Dict:
        """Parse input arguments to a dict."""
        slug = args["city"]
        if not slug:
            raise AssertionError("You must specify the city name.")
        self.slug = slug
        self.bbox = bbox
        self.city = city_name
        self._engine = self._create_engine()

    def _create_engine(self) -> Engine:
        """Sets up and returns a DB engine."""
        sql_url = get_connection_url(dbname="geoviz")
        engine = create_engine(sql_url)
        return engine.execution_options(
            schema_translate_map={"schema": self.slug}
        )

    def run(self):
        self._initialise_db()
        print("Fetching OSM data from overpass API...")
        pois = self._get_amenities()
        pois = pois.to_crs(epsg=3035)
        pois.geometry = pois.centroid
        pois = pois.to_crs(epsg=4326)

        pois = pois.reset_index()
        tag_columns = list(pois.columns)
        tag_columns.remove("osmid")
        tag_columns.remove("geometry")

        pois = pois.rename(columns={"osmid": "node_id"})
        pois = pois.rename(columns={"geometry": "geom"})
        pois = pois.set_index("node_id")
        pois["geom"] = pois["geom"].apply(lambda geom: WKTElement(geom.wkt, srid=4326))

        pois["tags"] = pois[tag_columns].apply(lambda x: x.to_json(), axis=1)
        pois = pois.drop(tag_columns, axis=1)

        pois.to_sql(name=OSMPoint.__tablename__, con=self._engine, schema=self.slug, if_exists="append",
                    dtype={"geom": Geometry(geometry_type="POINT", srid=4326)})

    def _initialise_db(self) -> None:
        """Initialises OSM points table and returns a new DB Session."""
        with self._engine.connect() as con:
            con.execute("CREATE EXTENSION postgis")
        self._engine.execute(CreateSchema(self.slug))

        OSMPoint.__table__.drop(self._engine, checkfirst=True)
        OSMPoint.__table__.create(self._engine)

    def _get_amenities(self):
        try:
            (minx, miny, maxx, maxy) = self.bbox
            return ox.geometries.geometries_from_bbox(maxy, miny, maxx, minx, tags=tags_to_filter)
        except (TypeError, ValueError):
            return ox.geometries.geometries_from_place(self.city, tags=tags_to_filter)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import OSM data for given bounding box."
    )
    parser.add_argument("--bbox", default=None, help="Boundingbox to import")
    parser.add_argument("--city", help="City to import")
    input_args = vars(parser.parse_args())

    OsmImporter(input_args).run()
