import argparse
import os
import sys
import re
import requests
from gtfs_functions import import_gtfs, stops_freq
from ipygis import get_connection_url
from shapely.geometry import Point
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from geoalchemy2.shape import from_shape
# test simple import now, convert to module later
sys.path.insert(0, "..")
from models import GTFSStop

GTFS_DATASETS = {
    "Helsinki": "https://transitfeeds.com/p/helsinki-regional-transport/735/latest/download",
    "Warsaw": "https://transitfeeds.com/p/ztm-warszawa/720/latest/download",
    "Copenhagen": "https://transitfeeds.com/p/rejseplanen/705/latest/download",
    "Tallinn": "https://transitfeeds.com/p/maanteeamet/510/latest/download",
    "Stockholm": "https://transitfeeds.com/p/storstockholms-lokaltrafik/1086/latest/download",
    "Saint Petersburg": "https://transitfeeds.com/p/saint-petersburg/826/latest/download",
    "Oslo": "https://transitfeeds.com/p/norsk-reiseinformasjon-as/791/latest/download",
    "Riga": "https://transitfeeds.com/p/rigas-satiksme/333/latest/download",
    "Berlin": "https://transitfeeds.com/p/verkehrsverbund-berlin-brandenburg/213/latest/download",
    "Hamburg": "https://transitfeeds.com/p/hamburger-verkehrsverbund-gmbh/1010/latest/download",
    "Munich": "https://transitfeeds.com/p/m-nchner-verkehrs-und-tarifverbund/1132/latest/download",
    "Amsterdam": "https://transitfeeds.com/p/ov/814/latest/download",
    "Vienna": "https://transitfeeds.com/p/stadt-wien/888/latest/download",
}

DATA_PATH = "data"


class GTFSImporter(object):
    def __init__(self, city: str = "", url: str = ""):
        if not city and not url:
            raise AssertionError("You must specify a city or GTFS feed url.")
        if url:
            self.url = url
        else:
            self.city = city
            self.url = GTFS_DATASETS.get(city, None)

        sql_url = get_connection_url(dbname="geoviz")
        engine = create_engine(sql_url)
        self.session = sessionmaker(bind=engine)()
        GTFSStop.__table__.create(engine, checkfirst=True)

    def run(self):
        if not self.url:
            print(f"GTFS data not found for {self.city}, skipping.")
            return
        filename = f"{DATA_PATH}/{self.city}.gtfs.zip"
        if os.path.isfile(filename):
            print("Found saved gtfs zip...")
        else:
            print("Downloading gtfs zip...")
            response = requests.get(self.url, allow_redirects=True)
            open(filename, 'wb').write(response.content)

        print("Loading gtfs zip...")
        routes, stops, stop_times, trips, shapes = import_gtfs(filename)
        # only calculate average daily frequency for all stops for now
        cutoffs = [0, 24]
        stop_frequencies = stops_freq(stop_times, stops, cutoffs)
        # only consider outbound departures for now
        stop_frequencies = stop_frequencies.loc[
            stop_frequencies["dir_id"] == "Outbound"
        ].to_dict(orient="records")
        stops_to_save = {}
        print(f"Found {len(stop_frequencies)} GTFS stops, importing...")
        for stop in stop_frequencies:
            stop_id = stop.pop("stop_id")
            geom = from_shape(stop.pop("geometry"), srid=4326)
            # use dict, since the json may contain the same stop twice!
            if stop_id in stops_to_save:
                print(f"Stop {stop_id} found twice, overwriting")
            # multiple cities may contain departures from the same stop. such
            # a stop is usually outside both cities (unless cities overlap).
            # overwrite existing data for the stop.
            stops_to_save[stop_id] = self.session.merge(
                GTFSStop(stop_id=stop_id, properties=stop, geom=geom)
            )
        print(f"Saving {len(stops_to_save)} GTFS stops...")
        # we cannot use bulk save, as we have to check for existing ids.
        # self.session.bulk_save_objects(stops_to_save.values())
        self.session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import GTFS data for given city or URL")
    parser.add_argument("--city", default="Helsinki", help="City to import")
    parser.add_argument("--url", default=None, help="GTFS url to import")
    args = vars(parser.parse_args())
    city = args.get("city", None)
    url = args.get("url", None)
    importer = GTFSImporter(city=city, url=url)
    importer.run()
