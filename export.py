#!/usr/bin/env python

import argparse
import logging
import os
import sys
from datasets import DATASETS
from ipygis import get_connection_url, QueryResult, generate_map
from slugify import slugify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import DropSchema
from notebooks.kepler_h3_config import config  # we may use our own custom visualization config
from osm_tags import tag_filter

IMPORT_LOG_PATH = 'logs'
MAPS_PATH = "server/maps"

parser = argparse.ArgumentParser(description="Create result map for a given city")
parser.add_argument("city", default="Helsinki", help="City to import")
parser.add_argument("--datasets",
                    default=" ".join([dataset for dataset in DATASETS]),
                    help="Datasets to include in analysis. Default is to use all imported data. E.g. \"osm access kontur\""
                    )
parser.add_argument("--delete",
                    action="store_true",
                    default=False,
                    help="Delete imported data from the database when the visualization is finished. Default is False."
                         " The result map is independent from the analysis database, so you may save a lot of disk space"
                         " by deleting the data if you don't expect to create the map again.")
args = vars(parser.parse_args())
# slugify city name just in case export was called with non-slug
city = slugify(args["city"])
datasets_to_export = args["datasets"].split()
delete = args.get("delete", False)

# log each city separately
log_file = os.path.join(os.path.dirname(__loader__.path), IMPORT_LOG_PATH, f"{city}.log")
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()
stdout_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(log_file)
logger.addFilter(stdout_handler)
logger.addHandler(file_handler)

sql_url = get_connection_url(dbname='geoviz')
engine = create_engine(sql_url)
schema_engine = engine.execution_options(
    schema_translate_map={'schema': city}
)
session = sessionmaker(bind=schema_engine)()

logger.info(f"Collecting results for {city} with {datasets_to_export}...")

queries = {
    dataset: session.query(DATASETS[dataset]['model'])
    for dataset in datasets_to_export
}
# osm query requires special filtering if we have extra nodes in the db
if 'osm' in queries:
    queries['osm'] = queries['osm'].filter(tag_filter)

logger.info(f"Running queries for {city} with {datasets_to_export}...")
results = [
    QueryResult.create(
        query,
        resolution=8,
        name=DATASETS[dataset]['name'],
        plot=DATASETS[dataset].get('plot', 'size'),
        group_by=DATASETS[dataset].get('group_by', None),
        column=DATASETS[dataset].get('column', None)
    )
    for dataset, query in queries.items()
]

logger.info(f"Creating map for {city} with {datasets_to_export}...")
weights = [
    DATASETS[dataset]['weight']
    for dataset in datasets_to_export
]
columns = [
    DATASETS[dataset].get('column', 'size').split('.')[-1]
    for dataset in datasets_to_export
]

result_map = generate_map(results, 500, config=config, column=columns, weights=weights, clusters=0.005)
map_path = os.path.join(os.path.dirname(__loader__.path), MAPS_PATH)
if not os.path.exists(map_path):
    os.mkdir(map_path)
filename = os.path.join(map_path, f"{city}.html")
result_map.save_to_html(file_name=filename)
# delete interim database at the end, we have all the data we need on the map
if delete:
    logger.info(f"Deleting analysis database for {city}...")
    engine.execute(DropSchema(city, cascade=True))

logger.info(f"--- Datasets {datasets_to_export} for {city} exported to Kepler.gl ---")
