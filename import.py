#!/usr/bin/env python

import argparse
import os
import requests
from dotenv import load_dotenv
from datasets import DATASETS
from scripts.import_flickr import FlickrImporter
from scripts.import_gtfs import GTFSImporter
from scripts.import_kontur import KonturImporter
from scripts.import_ookla import OoklaImporter
from scripts.import_osm_accessibility import AccessibilityImporter

CONTINENTS = [
    "europe",
    "africa",
    "asia",
    "north-america",
    "central-america",
    "south-america",
    "australia-oceania",
    "antarctica",
]
# some countries are known in nominatim, osmextracts and geofabrik by different names
# even with the same en language code :(
# format is "nominatim-name": "pbf-name"
COUNTRIES = {
    "czechia": "czech-republic"
}

load_dotenv()
osm_extracts_api_key = os.getenv("OSM_EXTRACTS_API_KEY")

parser = argparse.ArgumentParser(description="Import all datasets for a given city")
parser.add_argument("city", default="Helsinki", help="City to import")
parser.add_argument("--gtfs", help="Optional GTFS feed URL")
parser.add_argument("--datasets",
                    default=" ".join([dataset[0] for dataset in DATASETS]),
                    help="Datasets to import. Default is to import all. E.g. \"osm access kontur\""
                    )
parser.add_argument("--bbox", help="Use different bbox for the city. Format \"minx miny maxx maxy\"")

args = vars(parser.parse_args())
city = args["city"]
datasets = args["datasets"].split()
gtfs_url = args.get("gtfs", None)
bbox = args.get("bbox", None)
print(f"--- Importing datasets {datasets} for {city} ---")

# Get bbox, centroid and country for the city
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
bbox = [float(coord) for coord in bbox]
centroid = [city_data["lon"], city_data["lat"]]

country_params = {
    "lat": centroid[1],
    "lon": centroid[0],
    "zoom": 3,
    "format": "json",
    "namedetails": 1,
}
country_data = requests.get(
    "https://nominatim.openstreetmap.org/reverse", params=country_params
).json()
country = country_data["namedetails"]["name:en"]

print(f"{city} bounding box {bbox}")
print(f"{city} centroid {centroid}")
print(f"{city} country {country}")

country = country.lower()
# some countries are known in nominatim, osmextracts and geofabrik by different names
if country in COUNTRIES:
    country = COUNTRIES[country]

# OSM data needs to be imported first, will create the database
if "osm" in datasets:
    print(f"--- Importing OSM data for {city} ---")
    for continent in CONTINENTS:
        # Nominatim does not provide us with the continent. Will have to do some guessing
        if not os.system(f"./scripts/import_osm.sh {continent} {country} \"{city.lower()}\" {osm_extracts_api_key}"):
            break

if "flickr" in datasets:
    print(f"--- Importing Flickr data for {city} ---")
    # flickr wants the bbox as (minx, miny, maxx, maxy) string for now
    flick_importer = FlickrImporter(
        bbox=bbox
    )
    flick_importer.run()

if "gtfs" in datasets:
    # GTFS importer uses the provided URL or, failing that, default values for some cities
    if gtfs_url:
        print(f"--- Importing GTFS data from {gtfs_url} ---")
        gtfs_importer = GTFSImporter(url=gtfs_url, city=city)
    else:
        print(f"--- Importing GTFS data for {city} ---")
        gtfs_importer = GTFSImporter(city=city)
    gtfs_importer.run()

if "access" in datasets:
    print(f"--- Importing OSM walkability & accessibility data for {city} ---")
    # osmnx wants the bbox as minx, miny, maxx, maxy floats for now
    accessibility_importer = AccessibilityImporter(*bbox)
    accessibility_importer.run()

if "ookla" in datasets:
    print(f"--- Importing Ookla speedtest data for {city} ---")
    # ookla importer wants the bbox as minx, miny, maxx, maxy floats for now
    ookla_importer = OoklaImporter(
        city=city,
        bbox=bbox
    )
    ookla_importer.run()

if "kontur" in datasets:
    print(f"--- Importing Kontur population data for {city} ---")
    # kontur importer wants the bbox as minx, miny, maxx, maxy floats for now
    kontur_importer = KonturImporter(
        city=city,
        bbox=bbox
    )
    kontur_importer.run()

print(f"--- Datasets {datasets} for {city} imported to PostGIS ---")
