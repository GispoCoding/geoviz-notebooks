import argparse
import logging
from logging import Logger
import os
import sys
import requests
import shapefile
import shutil
import zipfile
from ipygis import get_connection_url
from osgeo import gdal
from shapely.geometry import Polygon
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List
from geoalchemy2.shape import from_shape
from slugify import slugify

# test simple import now, convert to module later
sys.path.insert(0, "..")
from models import OoklaPoint

DATA_PATH = "data"


class OoklaImporter(object):

    def __init__(self, slug: str, city: str, bbox: List[float], logger: Logger):
        if not city or not slug:
            raise AssertionError("You must specify the city name.")
        # BBOX (minx, miny, maxx, maxy)
        self.bbox = bbox
        self.city = city
        self.logger = logger
        self.download_url = "https://ookla-open-data.s3.amazonaws.com/shapefiles/performance/type=fixed/year=2021/quarter=1/"
        self.download_name = "2021-01-01_performance_fixed_tiles"

        # data should be stored one directory level above importers
        self.unzipped_path = os.path.join(
            os.path.dirname(os.path.dirname(__loader__.path)),
            DATA_PATH,
            self.download_name
        )
        self.download_file = self.unzipped_path + ".zip"
        self.city_file = f"{self.unzipped_path}/{self.city}.shp"

        sql_url = get_connection_url(dbname="geoviz")
        engine = create_engine(sql_url)
        schema_engine = engine.execution_options(
            schema_translate_map={'schema': slug}
        )
        self.session = sessionmaker(bind=schema_engine)()
        OoklaPoint.__table__.drop(schema_engine, checkfirst=True)
        OoklaPoint.__table__.create(schema_engine)

    def run(self):
        if os.path.isfile(self.download_file):
            self.logger.info("Found saved Ookla data...")
        else:
            self.logger.info("Downloading Ookla data...")
            self.logger.info(f"{self.download_url}{self.download_name}.zip")
            with requests.get(f"{self.download_url}{self.download_name}.zip", stream=True) as request:
                with open(self.download_file, 'wb') as file:
                    shutil.copyfileobj(request.raw, file)
        if not os.path.isdir(self.unzipped_path) or not os.path.isfile(f"{self.unzipped_path}/gps_fixed_tiles.shp"):
            self.logger.info("Extracting zip...")
            with zipfile.ZipFile(self.download_file, 'r') as zip_ref:
                zip_ref.extractall(self.unzipped_path)

        if not os.path.isfile(self.city_file):
            self.logger.info(f"Extracting {self.city} from Ookla data...")
            gdal.UseExceptions()
            # this does the same as ogr2ogr
            # https://gdal.org/python/osgeo.gdal-module.html#VectorTranslateOptions
            city_data = gdal.VectorTranslate(
                self.city_file,
                f"{self.unzipped_path}/gps_fixed_tiles.shp",
                spatFilter=self.bbox
            )
            self.logger.info(city_data)
            # we must dereference the data for the file actually to be written
            # https://gdal.org/api/python_gotchas.html#saving-and-closing-datasets-datasources
            del city_data
        else:
            self.logger.info(f"Found shapefile for {self.city}...")
        self.logger.info(f"Reading Ookla data for {self.city}...")
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
                points_to_save[quadkey_id] = OoklaPoint(
                    quadkey_id=quadkey_id, properties=properties, geom=geom
                )
                self.logger.info(geom)
                self.logger.info(properties)
        self.logger.info(f"Saving {len(points_to_save)} Ookla points...")
        self.session.bulk_save_objects(points_to_save.values())
        self.session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import Ookla speedtest data for given city")
    parser.add_argument("--city", default="Helsinki", help="City to import")
    parser.add_argument("--bbox", default=(24.82345, 60.14084, 25.06404, 60.29496))
    args = vars(parser.parse_args())
    arg_city = args.get("city", None)
    arg_slug = slugify(arg_city)
    arg_bbox = args.get("bbox", None)
    arg_bbox = list(map(float, arg_bbox.split(", ")))
    importer = OoklaImporter(arg_slug, arg_city, arg_bbox, logging.getLogger("import"))
    importer.run()
