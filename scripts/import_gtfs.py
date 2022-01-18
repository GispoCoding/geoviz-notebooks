import argparse
import logging
import os
import sys
import requests
from typing import List

from slugify import slugify
from gtfs_functions import import_gtfs, stops_freq
from ipygis import get_connection_url
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

logger = logging.getLogger("import")


class GTFSImporter(object):
    def __init__(self, slug: str, city: str, url: str = "", bbox: List[float] = None):
        if not city or not slug:
            raise AssertionError("You must specify the city name.")
        self.city = city
        # optional bbox allows filtering gtfs layer
        self.bbox = bbox
        if url:
            self.url = url
        else:
            self.url = GTFS_DATASETS.get(city, None)

        sql_url = get_connection_url(dbname="geoviz")
        engine = create_engine(sql_url)
        schema_engine = engine.execution_options(
            schema_translate_map={'schema': slug}
        )
        self.session = sessionmaker(bind=schema_engine)()
        GTFSStop.__table__.drop(schema_engine, checkfirst=True)
        GTFSStop.__table__.create(schema_engine)

    def run(self):
        if not self.url:
            logger.error(f"GTFS data not found for {self.city}, skipping.")
            return
        # data should be stored one directory level above importers
        filename = os.path.join(
            os.path.dirname(os.path.dirname(__loader__.path)),
            DATA_PATH,
            f"{self.city}.gtfs.zip"
        )
        if os.path.isfile(filename):
            logger.info("Found saved gtfs zip...")
        else:
            logger.info("Downloading gtfs zip...")
            response = requests.get(self.url, allow_redirects=True)
            open(filename, 'wb').write(response.content)

        logger.info("Loading gtfs zip...")
        routes, stops, stop_times, trips, shapes = import_gtfs(filename)
        # TODO: delete file after reading, we don't want to keep caching them all?
        # This is the only large dataset we download separately. or is gtfs data valuable?

        # only analyze stops within bbox, to cut down processing time
        # luckily, we have nifty bbox filtering available for geodataframes
        # https://geopandas.org/docs/user_guide/indexing.html
        if self.bbox:
            logger.info("Filtering gtfs data with bbox...")
            logger.info(self.bbox)
            stops = stops.cx[self.bbox[0]:self.bbox[2], self.bbox[1]:self.bbox[3]]
            stop_times = stop_times.cx[self.bbox[0]:self.bbox[2], self.bbox[1]:self.bbox[3]]

        # only calculate average daily frequency for all stops for now
        cutoffs = [0, 24]
        logger.info("Calculating stop frequencies...")
        stop_frequencies = stops_freq(stop_times, stops, cutoffs)
        # only consider outbound departures for now
        outbound_frequencies = stop_frequencies.loc[
            stop_frequencies["dir_id"] == "Outbound"
        ].to_dict(orient="records")
        # Some feeds don't have two directions. In that case, all
        # stops are inbound
        if not outbound_frequencies:
            outbound_frequencies = stop_frequencies.to_dict(orient="records")
        stops_to_save = {}
        logger.info(f"Found {len(outbound_frequencies)} GTFS stops, importing...")
        for stop in outbound_frequencies:
            stop_id = stop.pop("stop_id")
            geom = from_shape(stop.pop("geometry"), srid=4326)
            # use dict, since the json may contain the same stop twice!
            if stop_id in stops_to_save:
                logger.info(f"Stop {stop_id} found twice, overwriting")
            stops_to_save[stop_id] = GTFSStop(stop_id=stop_id, properties=stop, geom=geom)
        logger.info(f"Saving {len(stops_to_save)} GTFS stops...")
        self.session.bulk_save_objects(stops_to_save.values())
        self.session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import GTFS data for given city or URL")
    parser.add_argument("--city", default="Helsinki", help="City to import")
    parser.add_argument("--url", default=None, help="GTFS url to import")
    args = vars(parser.parse_args())
    arg_city = args.get("city", None)
    arg_slug = slugify(arg_city)
    arg_url = args.get("url", None)
    importer = GTFSImporter(slug=arg_slug, city=arg_city, url=arg_url)
    importer.run()
