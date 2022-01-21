#!/usr/bin/env python

import argparse
import copy
import datetime
import os
import requests
from dotenv import load_dotenv
from datasets import DATASETS
from geoalchemy2.shape import from_shape
from ipygis import get_connection_url
from scripts.import_flickr import FlickrImporter
from scripts.import_gtfs import GTFSImporter
from scripts.import_kontur import KonturImporter
from scripts.import_ookla import OoklaImporter
from scripts.import_osm import OsmImporter
from scripts.import_osm_accessibility import AccessibilityImporter
from shapely.geometry import box
from slugify import slugify
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema
from sqlalchemy_utils.functions import database_exists, create_database

from models import Analysis
from util import create_logger

load_dotenv()
osm_extracts_api_key = os.getenv("OSM_EXTRACTS_API_KEY")
osmnames_url = os.getenv("OSMNAMES_URL")

parser = argparse.ArgumentParser(description="Import all datasets for a given city")
parser.add_argument("city", default="Helsinki", help="City to import")
parser.add_argument("--gtfs", help="Optional GTFS feed URL")
parser.add_argument("--datasets",
                    default=" ".join([dataset for dataset in DATASETS]),
                    help="Datasets to import. Default is to import all. E.g. \"osm access kontur\""
                    )
parser.add_argument("--bbox", help="Use different bbox for the city. Format \"minx miny maxx maxy\"")
parser.add_argument("--export",
                    action="store_true",
                    default=False,
                    help="Automatically run analysis and create result map at the end of import.",
                    )
parser.add_argument("--delete",
                    action="store_true",
                    default=False,
                    help="Delete imported data from the database when the visualization is finished. Default is False."
                         " The result map is independent from the analysis database, so you may save a lot of disk space"
                         " by deleting the data if you don't expect to create the map again.")

args = vars(parser.parse_args())
city = args["city"]
slug = slugify(city)
dataset_string = args["datasets"]
datasets = dataset_string.split()
gtfs_url = args.get("gtfs", None)
bbox = args.get("bbox", None)
export = args.get("export", False)
delete = args.get("delete", False)

# log each city separately
logger = create_logger(slug)
logger.info(f"--- Importing datasets {datasets} for {city} ---")

if osmnames_url:
    # Use our own geocoding service. It provides bbox and country for city.
    logger.info(f"Geocoding {city} using OSMNames service at {osmnames_url}...")
    city_data = requests.get(
        f"{osmnames_url}/q/{city}.js"
    ).json()["results"][0]
    if bbox:
        bbox = bbox.split()
    else:
        bbox = city_data["boundingbox"]
else:
    # Fall back to Nominatim. Their API doesn't always respond tho.
    # Get bbox, centroid and country for the city
    logger.info(f"Geocoding {city} using Nominatim...")
    city_params = {"q": args["city"], "limit": 1, "format": "json"}
    city_data = requests.get(
        "https://nominatim.openstreetmap.org/search", params=city_params
    ).json()[0]
    if bbox:
        bbox = bbox.split()
    else:
        # nominatim returns miny, maxy, minx, maxx
        # we want minx, miny, maxx, maxy
        bbox = [city_data["boundingbox"][i] for i in [2, 0, 3, 1]]
    centroid = [city_data["lon"], city_data["lat"]]
    logger.info(f"{city} centroid: {centroid}")

# bbox must always be float
bbox = [float(coord) for coord in bbox]

# save all analysis requests to the db
sql_url = get_connection_url(dbname="geoviz")
# create db if this is the first run
if not database_exists(sql_url):
    create_database(sql_url)
engine = create_engine(sql_url)
session = sessionmaker(bind=engine)()
Analysis.__table__.create(engine, checkfirst=True)
analysis = Analysis(
    slug=slug,
    name=city,
    bbox=from_shape(box(*[float(coord) for coord in bbox])),
    # mark datasets like {selected: ['osm', 'flickr'], imported: ['osm']}
    datasets={"selected": datasets, "imported": []},
    # mark params like {gtfs: {url: http://example.com}}
    parameters={'gtfs': {'url': gtfs_url}}
)
session.add(analysis)

try:
    session.commit()
except IntegrityError:
    session.rollback()
    # there is an analysis for the city already. merge the datasets
    logger.info(f"Analysis for {city} found already. Overwriting selected datasets.")
    analysis = session.query(Analysis).filter(Analysis.slug == slug).first()
    analysis.bbox = from_shape(box(*[float(coord) for coord in bbox]))
    analysis.viewed = False
    analysis.finish_time = None
    if gtfs_url:
        analysis.parameters = {'gtfs': {'url': gtfs_url}}
    analysis.datasets = copy.deepcopy(analysis.datasets)
    analysis.datasets["selected"] = datasets
    session.commit()

# create schema for the analysis
try:
    engine.execute(CreateSchema(slug))
except ProgrammingError:
    # the schema may exist if some datasets have already been imported
    pass


# save analysis progress to the db as well
def mark_imported(dataset: str):
    # we must create a whole new datasets dict to update the binary object in db
    analysis.datasets = copy.deepcopy(analysis.datasets)
    analysis.datasets["imported"].append(dataset)
    session.commit()


logger.info(f"{city} bounding box {bbox}")

if "osm" in datasets:
    logger.info(f"--- Importing OSM data for {city} ---")
    osm_bbox = ", ".join([str(coord) for coord in bbox])
    osm_importer = OsmImporter({"slug": slug, "bbox": osm_bbox}, logger)
    osm_importer.run()
    mark_imported("osm")

if "flickr" in datasets:
    logger.info(f"--- Importing Flickr data for {city} ---")
    flick_importer = FlickrImporter(slug, bbox, logger)
    flick_importer.run()
    mark_imported("flickr")

if "gtfs" in datasets:
    # GTFS importer uses the provided URL or, failing that, default values for some cities
    if gtfs_url:
        logger.info(f"--- Importing GTFS data from {gtfs_url} ---")
        gtfs_importer = GTFSImporter(slug, city, logger, gtfs_url, bbox)
    else:
        logger.info(f"--- Importing GTFS data for {city} ---")
        gtfs_importer = GTFSImporter(slug, city, logger, bbox=bbox)
    gtfs_importer.run()
    mark_imported("gtfs")

if "access" in datasets:
    logger.info(f"--- Importing OSM walkability & accessibility data for {city} ---")
    accessibility_importer = AccessibilityImporter(slug, bbox, logger)
    accessibility_importer.run()
    mark_imported("access")

if "ookla" in datasets:
    logger.info(f"--- Importing Ookla speedtest data for {city} ---")
    ookla_importer = OoklaImporter(slug, city, bbox, logger)
    ookla_importer.run()
    mark_imported("ookla")

if "kontur" in datasets:
    logger.info(f"--- Importing Kontur population data for {city} ---")
    kontur_importer = KonturImporter(slug, city, bbox, logger)
    kontur_importer.run()
    mark_imported("kontur")

logger.info(f"--- Datasets {datasets} for {city} imported to PostGIS ---")

if export:
    logger.info(f"--- Creating result map for {city} ---")
    export_string = f"export.py {slug} --datasets \'{dataset_string}\'"
    if delete:
        export_string += " --delete"
    export_path = os.path.join(os.path.dirname(__loader__.path), export_string)
    os.system(export_path)

analysis.finish_time = datetime.datetime.now()
session.commit()
