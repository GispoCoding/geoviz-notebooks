#!/usr/bin/env python

import argparse
import os
from datasets import DATASETS
from ipygis import get_connection_url, QueryResult, generate_map
from slugify import slugify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import DropSchema
from notebooks.kepler_h3_config import config  # we may use our own custom visualization config
from osm_tags import tag_filter

from util import create_logger

MAPS_PATH = "server/maps"

parser = argparse.ArgumentParser(description="Create result map for a given city")
parser.add_argument("city_slug", default="helsinki", help="Slug of city to import")
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
slug = slugify(args["city_slug"])
datasets_to_export = args["datasets"].split()
delete = args.get("delete", False)

# log each city separately
logger = create_logger(slug)

sql_url = get_connection_url(dbname='geoviz')
engine = create_engine(sql_url)
schema_engine = engine.execution_options(
    schema_translate_map={'schema': slug}
)
session = sessionmaker(bind=schema_engine)()

logger.info(f"Collecting results for {slug} with {datasets_to_export}...")

queries = {
    dataset: session.query(DATASETS[dataset]['model'])
    for dataset in datasets_to_export
}
# osm query requires special filtering if we have extra nodes in the db
if 'osm' in queries:
    queries['osm'] = queries['osm'].filter(tag_filter)

logger.info(f"Running queries for {slug} with {datasets_to_export}...")
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

logger.info(f"Creating map for {slug} with {datasets_to_export}...")
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
filename = os.path.join(map_path, f"{slug}.html")
result_map.save_to_html(file_name=filename)
# delete interim database at the end, we have all the data we need on the map
if delete:
    logger.info(f"Deleting analysis database for {slug}...")
    engine.execute(DropSchema(slug, cascade=True))

logger.info(f"--- Datasets {datasets_to_export} for {slug} exported to Kepler.gl ---")
