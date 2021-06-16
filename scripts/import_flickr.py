import json
import sys
from ipygis import get_connection_url
from shapely.geometry import Point
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from geoalchemy2.shape import from_shape

# test simple import now, convert to module later
sys.path.insert(0, "..")
from models import FlickrPoint

sql_url = get_connection_url(dbname="geoviz")
engine = create_engine(sql_url)
session = sessionmaker(bind=engine)()
FlickrPoint.__table__.create(engine, checkfirst=True)

# TODO: run the import here instead of reading json file
json_file = open("flickr_HEL_comp_2020.json", "r")
points_to_import = json.load(json_file)
flickr_points = {}
print("Reading points to import...")
for point in points_to_import:
    pid = point.pop("id")
    geom = from_shape(Point(float(point.pop("latitude")), float(point.pop("longitude"))), srid=4326)
    # use dict, since the json may contain the same image twice!
    print(f"Image {pid} found twice, overwriting")
    flickr_points[pid] = FlickrPoint(point_id=pid, properties=point, geom=geom)
session.bulk_save_objects(flickr_points.values())
session.commit()
