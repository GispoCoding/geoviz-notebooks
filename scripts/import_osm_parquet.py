import glob
import os
from numpy import ndarray
import pandas as pd
import sys
import zipfile
from ipygis import get_connection_url
from shapely.geometry import Point
from sqlalchemy import create_engine, func, Index
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified
from geoalchemy2.shape import from_shape

# test simple import now, convert to module later
sys.path.insert(0, "..")
from models import OSMPoint, PopulationHex

DATA_PATH = "data"


class OSMParquetImporter(object):

    def __init__(self):
        # # BBOX (minx, miny, maxx, maxy)
        # self.bbox = bbox
        # self.city = city
        self.country = 'Finland'
        self.download_name = f"osm_pois_{self.country.lower()}.parquet"
        self.download_file = f"{DATA_PATH}/{self.download_name}.zip"
        self.unzipped_path = f"{DATA_PATH}/{self.download_name}"
        # self.city_file = f"{self.unzipped_path}/{self.city}.shp"

        sql_url = get_connection_url(dbname="geoviz-parquet")
        # Postgis intersection FROM queries are Cartesian products by definition, do not lint them
        engine = create_engine(sql_url, enable_from_linting=False)
        self.session = sessionmaker(bind=engine)()
        OSMPoint.__table__.create(engine, checkfirst=True)
        print("Creating extra spatial index in EPSG:3067...")
        # TODO: add spatial index for 3067
        idx_osmpoints_geom_3067 = Index(
            'idx_osmpoints_geom_3067',
            OSMPoint.geom.ST_Transform(3067),
            postgresql_using='gist'
            )
        idx_osmpoints_geom_3067.create(bind=engine)

    def run(self):
        if os.path.isfile(self.download_file):
            print("Found saved OSM Parquet data...")
        if not os.path.isdir(self.unzipped_path):
            print("Extracting zip...")
            with zipfile.ZipFile(self.download_file, 'r') as zip_ref:
                zip_ref.extractall(self.unzipped_path)

        print(f"Reading OSM POIs for {self.country}...")
        print(f"{self.unzipped_path}/part-*.parquet")
        points_to_save = {}

        def add_point(point: ndarray):
            id, tags, lat, lon, hex = point[1:6]
            # ndarray is not json serializable as-is
            tags = tags.tolist()
            geom = from_shape(Point(lat, lon), srid=4326)

            points_to_save[id] = OSMPoint(
                node_id=id, tags=tags, geom=geom
            )

        for part in glob.glob(f"{self.unzipped_path}/part-*.parquet"):
            print(f"Reading parquet file {part}")
            data = pd.read_parquet(part, engine='pyarrow')
            pois = data[data['osm_type'] == 'node']
            print(f"Found {len(pois)} osm nodes")
            # this seems the most efficient way to loop in pandas
            pois.apply(add_point, raw=True, axis=1)
            # if points_to_save:
            #     # only import first file
            #     break
        print(f"Saving {len(points_to_save)} OSM points...")
        self.session.bulk_save_objects(points_to_save.values())
        self.session.commit()

        # in case population hexes have been imported, calculate the local populations here
        # This returns all the hexes around each node
        # https://github.com/kuwala-io/kuwala/blob/master/kuwala/core/neo4j/plugins/udfs/src/main/java/io/kuwala/h3/H3.java#L35
        fields = ['total', 'children_under_five', 'elderly_60_plus', 'men', 'women', 'women_of_reproductive_age_15_49', 'youth_15_24']
        print("Calculating population within 200 m of each point...")
        nodes_with_population_200 = self.session.query(
            OSMPoint,
            *[func.sum(getattr(PopulationHex, field)) for field in fields]
            ).filter(
                PopulationHex.geom.ST_Transform(3067).ST_Dwithin(
                    OSMPoint.geom.ST_Transform(3067), 200
                )
            ).group_by(OSMPoint.node_id).all()
        print("Saving population within 200 m of each point...")
        for osm_point, *populations in nodes_with_population_200:
            osm_point.populations_200 = {
                field: population for field, population in zip(fields, populations)
                }
            # sqlalchemy doesn't automatically detect changes in json(b) fields :(
            flag_modified(osm_point, 'populations_200')
            print(osm_point.populations_200)
        self.session.commit()
        print("Calculating population within 400 m of each point...")
        nodes_with_population_400 = self.session.query(
            OSMPoint,
            *[func.sum(getattr(PopulationHex, field)) for field in fields]
            ).filter(
                PopulationHex.geom.ST_Transform(3067).ST_Dwithin(
                    OSMPoint.geom.ST_Transform(3067), 400
                )
            ).group_by(OSMPoint.node_id).all()
        print("Saving population within 400 m of each point...")
        for osm_point, *populations in nodes_with_population_400:
            osm_point.populations_400 = {
                field: population for field, population in zip(fields, populations)
                }
            # sqlalchemy doesn't automatically detect changes in json(b) fields :(
            flag_modified(osm_point, 'populations_400')
            print(osm_point.populations_400)
        self.session.commit()
