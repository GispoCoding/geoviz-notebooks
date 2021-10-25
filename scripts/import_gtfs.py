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
    "Helsinki": "https://infopalvelut.storage.hsldev.com/gtfs/hsl.zip",
    "Turku": "http://data.foli.fi/gtfs/gtfs.zip",
    "Tampere": "http://data.itsfactory.fi/journeys/files/gtfs/latest/gtfs_tampere.zip",
    "Warsaw": "https://mkuran.pl/gtfs/warsaw.zip",
    "Copenhagen": "http://www.rejseplanen.info/labs/GTFS.zip",
    "Tallinn": "http://www.peatus.ee/gtfs/gtfs.zip",
    "Stockholm": "https://data.samtrafiken.se/trafiklab/gtfs-sverige-2/2021/08/sweden-20210827.zip",
    "Saint Petersburg": "https://transport.orgp.spb.ru/Portal/transport/internalapi/gtfs/feed.zip",
    "Oslo": "https://storage.googleapis.com/marduk-production/outbound/gtfs/rb_norway-aggregated-gtfs.zip",
    "Riga": "https://data.gov.lv/dati/dataset/6d78358a-0095-4ce3-b119-6cde5d0ac54f/resource/612b7cd9-fac1-4fbc-889e-e27f1a9dcaa5/download/marsrutusaraksti08_2021.zip",
    "Berlin": "https://www.vbb.de/fileadmin/user_upload/VBB/Dokumente/API-Datensaetze/GTFS.zip",
    "Hamburg": "http://daten.transparenz.hamburg.de/Dataport.HmbTG.ZS.Webservice.GetRessource100/GetRessource100.svc/74444c22-a877-4cea-90bf-aa5c94c88ae8/Upload__HVV_Rohdaten_GTFS_Fpl_20210805.zip",
    "Munich": "https://www.mvv-muenchen.de/fileadmin/mediapool/02-Fahrplanauskunft/03-Downloads/openData/mvv_gtfs.zip",
    "Amsterdam": "http://gtfs.ovapi.nl/nl/gtfs-nl.zip",
    "Vienna": "http://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/gtfs.zip",
    "Gdansk": "https://mkuran.pl/gtfs/tristar.zip",
    "Wroclaw": "https://www.wroclaw.pl/open-data/87b09b32-f076-4475-8ec9-6020ed1f9ac0/OtwartyWroclaw_rozklad_jazdy_GTFS.zip",
}

DATA_PATH = "data"


class GTFSImporter(object):
    def __init__(self, city: str, url: str = ""):
        if not city:
            raise AssertionError("You must specify the city name.")
        self.city = city
        if url:
            self.url = url
        else:
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
