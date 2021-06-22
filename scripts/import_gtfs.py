import sys
from gtfs_functions import import_gtfs, stops_freq
from ipygis import get_connection_url
from shapely.geometry import Point
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from geoalchemy2.shape import from_shape


# test simple import now, convert to module later
sys.path.insert(0, "..")
from models import GTFSStop

sql_url = get_connection_url(dbname="geoviz")
engine = create_engine(sql_url)
session = sessionmaker(bind=engine)()
GTFSStop.__table__.create(engine, checkfirst=True)

print("Loading gtfs zip...")
routes, stops, stop_times, trips, shapes = import_gtfs("helsinki.gtfs.zip")
# only calculate average daily frequency for all stops for now
cutoffs = [0, 24]
stop_frequencies = stops_freq(stop_times, stops, cutoffs)
# only consider outbound departures for now
stop_frequencies = stop_frequencies.loc[stop_frequencies["dir_id"] == "Outbound"].to_dict(orient='records')
stops_to_save = {}
print(f"Found {len(stop_frequencies)} GTFS stops, importing...")
for stop in stop_frequencies:
    stop_id = stop.pop("stop_id")
    geom = from_shape(stop.pop("geometry"), srid=4326)
    # use dict, since the json may contain the same stop twice!
    if stop_id in stops_to_save:
        print(f"Stop {stop_id} found twice, overwriting")
    stops_to_save[stop_id] = GTFSStop(stop_id=stop_id, properties=stop, geom=geom)
print(f"Saving {len(stops_to_save)} GTFS stops...")
session.bulk_save_objects(stops_to_save.values())
session.commit()
