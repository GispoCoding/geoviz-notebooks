import glob
import os
from numpy import ndarray
import pandas as pd
import re
import sys
import zipfile
from ipygis import get_connection_url
from shapely.geometry import Point
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from geoalchemy2.shape import from_shape

# test simple import now, convert to module later
sys.path.insert(0, "..")
from models import GooglePoint

DATA_PATH = "data"


class GoogleParquetImporter(object):

    def __init__(self, city: str = 'Helsinki'):
        # # BBOX (minx, miny, maxx, maxy)
        # self.bbox = bbox
        self.city = city
        self.download_name = f"google_pois_{self.city.lower()}.parquet"
        self.download_file = f"{DATA_PATH}/{self.download_name}.zip"
        self.unzipped_path = f"{DATA_PATH}/{self.download_name}"

        sql_url = get_connection_url(dbname="geoviz-parquet")
        engine = create_engine(sql_url)
        self.session = sessionmaker(bind=engine)()
        GooglePoint.__table__.create(engine, checkfirst=True)

    def run(self):
        if os.path.isfile(self.download_file):
            print("Found saved OSM Parquet data...")
        if not os.path.isdir(self.unzipped_path):
            print("Extracting zip...")
            with zipfile.ZipFile(self.download_file, 'r') as zip_ref:
                zip_ref.extractall(self.unzipped_path)

        print(f"Reading Google POIs for {self.city}...")
        print(f"{self.unzipped_path}/part-*.parquet")
        points_to_save = {}

        morning = r"T0[0-9]:00"
        noon = r"T1[0-3]:00"
        afternoon = r"T1[4-7]:00"

        def aggregate_popularity(popularity: ndarray):
            aggregate_by_time = {
                'morning': 0,
                'noon': 0,
                'afternoon': 0,
                'evening': 0,
                'total': 0
            }
            for datum in popularity:
                aggregate_by_time['total'] += datum['popularity']
                if re.search(morning, datum['timestamp']):
                    print('found morning')
                    aggregate_by_time['morning'] += datum['popularity']
                elif re.search(noon, datum['timestamp']):
                    print('found noon')
                    aggregate_by_time['noon'] += datum['popularity']
                elif re.search(afternoon, datum['timestamp']):
                    print('found afternoon')
                    aggregate_by_time['afternoon'] += datum['popularity']
                else:
                    print('found evening')
                    aggregate_by_time['evening'] += datum['popularity']
            return aggregate_by_time

        def add_point(point: ndarray):
            id = point[3]
            osm_node_id = point[0]
            popularity = point[18]
            location = point[6]

            if popularity is not None:
                popularity = aggregate_popularity(popularity)
            geom = from_shape(Point(location['lat'], location['lng']), srid=4326)
            points_to_save[id] = GooglePoint(
                node_id=id, osm_node_id=osm_node_id, popularity=popularity, geom=geom
            )

        for part in glob.glob(f"{self.unzipped_path}/part-*.parquet"):
            print(f"Reading parquet file {part}")
            data = pd.read_parquet(part, engine='pyarrow')
            pois = data[data['type'] == 'node']
            print(f"Found {len(pois)} google nodes")
            # this seems the most efficient way to loop in pandas
            pois.apply(add_point, raw=True, axis=1)
        print(f"Saving {len(points_to_save)} Google points...")
        self.session.bulk_save_objects(points_to_save.values())
        self.session.commit()
