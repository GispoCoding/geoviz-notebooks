#!/usr/bin/env python

import argparse
import os
import requests
from dotenv import load_dotenv
from scripts.import_population_parquet import PopulationParquetImporter
from scripts.import_osm_parquet import OSMParquetImporter
from scripts.import_google_parquet import GoogleParquetImporter

parser = argparse.ArgumentParser(description="Import all datasets for a given city")
# parser.add_argument("city", default="Helsinki", help="City to import")
parser.add_argument("--datasets",
                    default="population-parquet osm-parquet google-parquet",
                    help="Datasets to import. Default is to import all."
                    )

args = vars(parser.parse_args())
# city = args["city"]
datasets = args["datasets"].split()
# gtfs_url = args.get("gtfs_url", None)
# bbox = args.get("bbox", None)
# print(f"--- Importing datasets {datasets} for {city} ---")

# # Get bbox, centroid and country for the city
# city_params = {"q": args["city"], "limit": 1, "format": "json"}
# city_data = requests.get(
#     "https://nominatim.openstreetmap.org/search", params=city_params
# ).json()[0]
# if bbox:
#     bbox = bbox.split()
# else:
#     # nominatim returns miny, maxy, minx, maxx
#     # we want minx, miny, maxx, maxy
#     bbox = [city_data["boundingbox"][i] for i in [2, 0, 3, 1]]
# bbox = [float(coord) for coord in bbox]
# centroid = [city_data["lon"], city_data["lat"]]

# country_params = {
#     "lat": centroid[1],
#     "lon": centroid[0],
#     "zoom": 3,
#     "format": "json",
#     "namedetails": 1,
# }
# country_data = requests.get(
#     "https://nominatim.openstreetmap.org/reverse", params=country_params
# ).json()
# country = country_data["namedetails"]["name:en"]

# print(f"{city} bounding box {bbox}")
# print(f"{city} centroid {centroid}")
# print(f"{city} country {country}")

# population must be imported first, so we can calculate populations for osm points
if "population-parquet" in datasets:
    print("--- Importing population parquet data ---")
    population_parquet_importer = PopulationParquetImporter()
    population_parquet_importer.run()

# osm points must be imported second, so we can link google pois to osm points
if "osm-parquet" in datasets:
    print("--- Importing OSM parquet POI data ---")
    osm_parquet_importer = OSMParquetImporter()
    osm_parquet_importer.run()

# google points must be imported last
if "google-parquet" in datasets:
    print("--- Importing google parquet data ---")
    google_parquet_importer = GoogleParquetImporter()
    google_parquet_importer.run()


print(f"--- Datasets {datasets} imported to PostGIS ---")
