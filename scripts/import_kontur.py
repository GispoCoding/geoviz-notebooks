import argparse
import fiona
import gzip
import os
import sys
import requests
import shutil
from ipygis import get_connection_url
from osgeo import gdal
from shapely.geometry import Point, Polygon
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Tuple
from geoalchemy2.shape import from_shape

# test simple import now, convert to module later
sys.path.insert(0, "..")
from models import KonturPoint

DATA_PATH = "data"


class KonturImporter(object):

    def __init__(self, city: str, bbox: Tuple):
        # BBOX (minx, miny, maxx, maxy)
        self.bbox = bbox
        self.city = city
        self.download_url = "https://adhoc.kontur.io/data/"
        self.download_name = "kontur_population_20200928.gpkg"

        # data should be stored one directory level above importers
        self.unzipped_file = os.path.join(
            os.path.dirname(os.path.dirname(__loader__.path)),
            DATA_PATH,
            self.download_name
        )
        self.download_file = self.unzipped_file + ".gz"
        self.city_file = f"{self.unzipped_file}_extracts/{self.city}.gpkg"

        sql_url = get_connection_url(dbname="geoviz")
        engine = create_engine(sql_url)
        self.session = sessionmaker(bind=engine)()
        KonturPoint.__table__.create(engine, checkfirst=True)

    def run(self):
        if os.path.isfile(self.download_file):
            print("Found saved Kontur data...")
        else:
            print("Downloading Kontur data...")
            print(f"{self.download_url}{self.download_name}.gz")
            with requests.get(f"{self.download_url}{self.download_name}.gz", stream=True) as request:
                with open(self.download_file, 'wb') as file:
                    shutil.copyfileobj(request.raw, file)
        if not os.path.isfile(self.unzipped_file):
            print("Extracting gz...")
            with gzip.open(self.download_file, 'rb') as gzip_file:
                with open(self.unzipped_file, 'wb') as out_file:
                    shutil.copyfileobj(gzip_file, out_file)

        if not os.path.isfile(self.city_file):
            if not os.path.isdir(f"{self.unzipped_file}_extracts"):
                os.mkdir(f"{self.unzipped_file}_extracts")
            print(f"Extracting {self.city} from Kontur data...")
            gdal.UseExceptions()
            # this does the same as ogr2ogr
            # https://gdal.org/python/osgeo.gdal-module.html#VectorTranslateOptions
            # we must specify filter SRS, since the geopackage is in 3857
            city_data = gdal.VectorTranslate(
                self.city_file,
                self.unzipped_file,
                spatFilter=self.bbox,
                spatSRS="EPSG:4326"
            )
            # we must dereference the data for the file actually to be written
            # https://gdal.org/api/python_gotchas.html#saving-and-closing-datasets-datasources
            del city_data
        else:
            print(f"Found geopackage for {self.city}...")
        print(f"Reading Kontur data for {self.city}...")
        points_to_save = {}
        for layer_name in fiona.listlayers(self.city_file):
            with fiona.open(self.city_file, layer=layer_name) as source:
                for record in source:
                    polygon = Polygon(record["geometry"]["coordinates"][0])
                    # Kontur records are saved per resolution=8 H3 hex
                    # We only need centroids. Note that these cannot be used for
                    # analyses at resolution 9 or above as such: data would
                    # be mapped to the central hex instead of spread out across seven.
                    # TODO: should we save polygons, to allow high resolution analyses?
                    geom = from_shape(polygon.centroid, srid=3857)
                    properties = record["properties"]
                    hex_id = record["id"]
                    # multiple cities may contain the same hexes, if the bboxes overlap.
                    # overwrite existing data for the hexes.
                    points_to_save[hex_id] = self.session.merge(
                        KonturPoint(hex_id=hex_id, properties=properties, geom=geom)
                    )
        print(f"Saving {len(points_to_save)} Kontur points...")
        # we cannot use bulk save, as we have to check for existing ids.
        # self.session.bulk_save_objects(points_to_save.values())
        self.session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import Kontur population data for given city")
    parser.add_argument("--city", default="Helsinki", help="City to import")
    parser.add_argument("--bbox", default=(24.82345, 60.14084, 25.06404, 60.29496))
    args = vars(parser.parse_args())
    city = args.get("city", None)
    bbox = args.get("bbox", None)
    importer = KonturImporter(city=city, bbox=bbox)
    importer.run()
