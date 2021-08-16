import argparse
import os
import requests
from dotenv import load_dotenv
from scripts.import_flickr import FlickrImporter
from scripts.import_gtfs import GTFSImporter
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
load_dotenv()
osm_extracts_api_key = os.getenv("OSM_EXTRACTS_API_KEY")

parser = argparse.ArgumentParser(description="Import all datasets for a given city")
parser.add_argument("city", default="Helsinki", help="City data to import")
parser.add_argument("--gtfs", help="Optional GTFS feed URL")
args = vars(parser.parse_args())
city = args["city"]
gtfs_url = args.get("gtfs_url", None)
print(f"--- Importing all datasets for {city} ---")

# Get bbox, centroid and country for the city
city_params = {"q": args["city"], "limit": 1, "format": "json"}
city_data = requests.get(
    "https://nominatim.openstreetmap.org/search", params=city_params
).json()[0]
bbox = city_data["boundingbox"]
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

# OSM data needs to be imported first, will create the database
print(f"--- Importing OSM data for {city} ---")
for continent in CONTINENTS:
    # Nominatim does not provide us with the continent. Will have to do some guessing
    if not os.system(f"./scripts/import_osm.sh {continent} {country.lower()} \"{city.lower()}\" {osm_extracts_api_key}"):
        break

print(f"--- Importing Flickr data for {city} ---")
# flickr wants the bbox as (minx, miny, maxx, maxy) string for now
flick_importer = FlickrImporter(
    bbox=f"{float(bbox[2])}, {float(bbox[0])}, {float(bbox[3])}, {float(bbox[1])}"
)
flick_importer.run()

# GTFS importer uses the provided URL or, failing that, default values for some cities
if gtfs_url:
    print(f"--- Importing GTFS data from {gtfs_url} ---")
    gtfs_importer = GTFSImporter(url=gtfs_url)
else:
    print(f"--- Importing GTFS data for {city} ---")
    gtfs_importer = GTFSImporter(city=city)
gtfs_importer.run()

print(f"--- Importing OSM walkability & accessibility data for {city} ---")
# osmnx wants the bbox as minx, miny, maxx, maxy floats for now
accessibility_importer = AccessibilityImporter(
    float(bbox[2]), float(bbox[0]), float(bbox[3]), float(bbox[1])
)
accessibility_importer.run()

print(f"--- All datasets for {city} imported to PostGIS ---")
