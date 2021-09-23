import glob
import os
import pandas as pd
import sys
import zipfile
from h3 import h3_to_geo
from ipygis import get_connection_url
from math import isnan
from numpy import ndarray
from shapely.geometry import Point
from sqlalchemy import create_engine, Index
from sqlalchemy.orm import sessionmaker
from geoalchemy2.shape import from_shape

# test simple import now, convert to module later
sys.path.insert(0, "..")
from models import PopulationHex

DATA_PATH = "data"


class PopulationParquetImporter(object):

    def __init__(self):
        # # BBOX (minx, miny, maxx, maxy)
        # self.bbox = bbox
        # self.city = city
        self.country = 'Finland'
        self.download_name = f"population_{self.country.lower()}.parquet"
        self.download_file = f"{DATA_PATH}/{self.download_name}.zip"
        self.unzipped_path = f"{DATA_PATH}/{self.download_name}"

        sql_url = get_connection_url(dbname="geoviz-parquet")
        engine = create_engine(sql_url)
        self.session = sessionmaker(bind=engine)()
        PopulationHex.__table__.create(engine, checkfirst=True)
        print("Creating extra spatial index in EPSG:3067...")
        # TODO: add spatial index for 3067
        idx_populationhexes_geom_3067 = Index(
            'idx_populationhexes_geom_3067',
            PopulationHex.geom.ST_Transform(3067),
            postgresql_using='gist'
            )
        idx_populationhexes_geom_3067.create(bind=engine)

    def run(self):
        if os.path.isfile(self.download_file):
            print("Found saved OSM Parquet data...")
        if not os.path.isdir(self.unzipped_path):
            print("Extracting zip...")
            with zipfile.ZipFile(self.download_file, 'r') as zip_ref:
                zip_ref.extractall(self.unzipped_path)

        print(f"Reading population data for {self.country}...")
        print(f"{self.unzipped_path}/part-*.parquet")
        hexes_to_save = {}

        def add_hex(hex: ndarray):
            populations = []
            id, *populations = hex
            # populations sometimes contain float(nan)s, they may crash psycopg2
            if any(isnan(value) for value in populations):
                populations = [None if isnan(value) else value
                               for value in populations]
            centroid = Point(h3_to_geo(id))
            geom = from_shape(centroid, srid=4326)
            hexes_to_save[id] = PopulationHex(
                hex_id=id,
                children_under_five=populations[0],
                elderly_60_plus=populations[1],
                total=populations[2],
                men=populations[3],
                women=populations[4],
                women_of_reproductive_age_15_49=populations[5],
                youth_15_24=populations[6],
                geom=geom
            )

        for part in glob.glob(f"{self.unzipped_path}/part-*.parquet"):
            print(f"Reading parquet file {part}")
            data = pd.read_parquet(part, engine='pyarrow')
            print(f"Found {len(data)} hexes")
            # this seems the most efficient way to loop in pandas
            data.apply(add_hex, raw=True, axis=1)
        print(f"Saving {len(hexes_to_save)} population hexes...")
        self.session.bulk_save_objects(hexes_to_save.values())
        self.session.commit()
