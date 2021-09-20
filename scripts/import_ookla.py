import argparse
import os
import sys
import re
import requests
import shapefile
import shutil
import zipfile
from ipygis import get_connection_url
from osgeo import gdal
from shapely.geometry import Point, Polygon
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Tuple
from geoalchemy2.shape import from_shape

# test simple import now, convert to module later
sys.path.insert(0, "..")
from models import OoklaPoint

DATA_PATH = "data"


class OoklaImporter(object):

    def __init__(self, city: str, bbox: Tuple):
        # BBOX (minx, miny, maxx, maxy)
        self.bbox = bbox
        self.city = city
        self.download_url = "https://ookla-open-data.s3.amazonaws.com/shapefiles/performance/type=fixed/year=2021/quarter=1/"
        self.download_name = "2021-01-01_performance_fixed_tiles"
        self.download_file = f"{DATA_PATH}/{self.download_name}.zip"
        self.unzipped_path = f"{DATA_PATH}/{self.download_name}"
        self.city_file = f"{self.unzipped_path}/{self.city}.shp"

        sql_url = get_connection_url(dbname="geoviz")
        engine = create_engine(sql_url)
        self.session = sessionmaker(bind=engine)()
        OoklaPoint.__table__.create(engine, checkfirst=True)

    def run(self):
        if os.path.isfile(self.download_file):
            print("Found saved Ookla data...")
        else:
            print("Downloading Ookla data...")
            print(f"{self.download_url}{self.download_name}.zip")
            with requests.get(f"{self.download_url}{self.download_name}.zip", stream=True) as request:
                with open(self.download_file, 'wb') as file:
                    shutil.copyfileobj(request.raw, file)
        if not os.path.isdir(self.unzipped_path):
            print("Extracting zip...")
            with zipfile.ZipFile(self.download_file, 'r') as zip_ref:
                zip_ref.extractall(self.unzipped_path)

        if not os.path.isfile(self.city_file):
            print(f"Extracting {self.city} from Ookla data...")
            gdal.UseExceptions()
            # this does the same as ogr2ogr
            # https://gdal.org/python/osgeo.gdal-module.html#VectorTranslateOptions
            city_data = gdal.VectorTranslate(
                self.city_file,
                f"{self.unzipped_path}/gps_fixed_tiles.shp",
                spatFilter=self.bbox
            )
            print(city_data)
            # we must dereference the data for the file actually to be written
            # https://gdal.org/api/python_gotchas.html#saving-and-closing-datasets-datasources
            del city_data
        else:
            print(f"Found shapefile for {self.city}...")
        print(f"Reading Ookla data for {self.city}...")
        with shapefile.Reader(self.city_file) as shapes:
            points_to_save = {}
            for shaperecord in shapes.shapeRecords():
                # Ookla records are saved per tile, we only need centroids.
                # Note that these cannot be used for analyses at resolution 9
                # or above as such: not all hexes would contain a tile centroid.
                # TODO: should we save polygons, to allow high resolution analyses?
                polygon = Polygon(shaperecord.shape.points)
                geom = from_shape(polygon.centroid, srid=4326)
                properties = shaperecord.record.as_dict()
                if properties["devices"] < 3:
                    # ignore polygons with only one or two devices
                    # outliers tell nothing of average speed in the area
                    # e.g. single people on an island or in the woods who have
                    # paid for fibre cable
                    continue
                quadkey_id = properties.pop("quadkey")
                # multiple cities may contain the same points, if the bboxes overlap.
                # overwrite existing data for the points.
                points_to_save[quadkey_id] = self.session.merge(
                    OoklaPoint(quadkey_id=quadkey_id, properties=properties, geom=geom)
                )
                print(geom)
                print(properties)
        print(f"Saving {len(points_to_save)} Ookla points...")
        # we cannot use bulk save, as we have to check for existing ids.
        # self.session.bulk_save_objects(points_to_save.values())
        self.session.commit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import Ookla speedtest data for given city")
    parser.add_argument("--city", default="Helsinki", help="City to import")
    parser.add_argument("--bbox", default=(24.82345, 60.14084, 25.06404, 60.29496))
    args = vars(parser.parse_args())
    city = args.get("city", None)
    bbox = args.get("bbox", None)
    importer = OoklaImporter(city=city, bbox=bbox)
    importer.run()
