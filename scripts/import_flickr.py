import argparse
import datetime
import os
import sys
from flickrapi import FlickrAPI, FlickrError
from dotenv import load_dotenv
from ipygis import get_connection_url
from logging import Logger
from shapely.geometry import Point
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Tuple
from geoalchemy2.shape import from_shape
# test simple import now, convert to module later
sys.path.insert(0, "..")
from models import FlickrPoint


class FlickrImporter:
    def __init__(self, slug: str, bbox: Tuple, logger: Logger):
        """Sets the initial parameters, connects to flickr and database"""

        self.logger = logger
        if not slug:
            raise AssertionError("You must specify the city name.")
        
        # BBOX (minx, miny, maxx, maxy)
        total_bbox = tuple(float(coord) for coord in bbox)
        # Set temporal extent
        end_date = datetime.datetime.today()
        start_date = end_date - datetime.timedelta(days=3*365)
        # List for api request parameter tuples
        self.start_params = [(total_bbox, start_date, end_date)]
        
        # List for photos
        self.photos = []
        # Keep track of queries
        self.q_count = 0

        # Connect to flickr
        load_dotenv()
        self.flickr = FlickrAPI(
            os.getenv("FLICKR_API_KEY"),
            os.getenv("FLICKR_SECRET"),
            format="parsed-json"
        )

        # Database
        sql_url = get_connection_url(dbname="geoviz")
        engine = create_engine(sql_url)
        schema_engine = engine.execution_options(
            schema_translate_map={'schema': slug}
        )
        self.session = sessionmaker(bind=schema_engine)()
        FlickrPoint.__table__.drop(schema_engine, checkfirst=True)
        FlickrPoint.__table__.create(schema_engine)


    def run(self):
        """Downloads photo locations and saves them to database"""

        # Download photos
        self.loop(self.start_params)
        
        # Save the photo locations
        flickr_points = {}
        self.logger.info(f"Found {len(self.photos)} flickr photos, importing...")
        for point in self.photos:
            pid = point.pop("id")
            geom = from_shape(
                Point(float(point.pop("longitude")),
                float(point.pop("latitude"))),
                srid=4326
            )
            # Use dict, since the json may contain the same image twice!
            if pid in flickr_points:
                self.logger.info(f"Image {pid} found twice, overwriting")
            flickr_points[pid] = FlickrPoint(point_id=pid, properties=point, geom=geom)
        self.logger.info(f"Saving {len(flickr_points)} flickr points...")
        self.session.bulk_save_objects(flickr_points.values())
        self.session.commit()


    def loop(self, params_list:list):
        """The main download loop
        
        Loops through the API request parameters in params_list, sends
        API queries and and creates a new parameter list as needed
        
        If new parameters are created, they are looped as a separate
        list after looping the current params_list is finished 
        """
        
        # A list for storing new params
        new_params = []

        for params in params_list:
            # bbox and dates as variabes
            self.bbox = params[0]
            self.min_date = params[1]
            self.max_date = params[2]
            self.min_date_str = (
                f"{self.min_date.year}-"
                f"{self.min_date.month:02}-"
                f"{self.min_date.day:02} 00:00:00"
            )
            self.max_date_str = (
                f"{self.max_date.year}-"
                f"{self.max_date.month:02}-"
                f"{self.max_date.day:02} 00:00:00"
            )
            # Print info
            self.logger.info(f"\nbbox: {self.bbox}")
            self.logger.info(f"  From: {self.min_date_str}")
            self.logger.info(f"  To:   {self.max_date_str}")

            # Start reading photos from page 1
            page = 1
            # Get photos
            while True:
                # Flickr's query limit
                if self.q_count > 3600:
                    raise AssertionError("query limit")

                # Query flickr
                photos_to_add = self.flickr_query(page)

                # If the query reaches the limit of 4000 photos (16*250=4000):
                if photos_to_add["pages"] > 16:
                    # Add new params and move to next params
                    self.add_new_params(new_params)
                    break

                # The query is small enough to download -> add photos    
                self.photos += photos_to_add["photo"]
                # Stop when photos from every page have been added
                if page >= photos_to_add["pages"]:
                    self.logger.info(f"    {photos_to_add['total']} photos added")
                    break
                # Move on to next page
                page += 1
        
        # See if any new params had to be created
        if len(new_params) > 0:
            # Loop with the new params
            self.logger.info("\n\nSwitching to a new parameter list")
            self.loop(new_params)


    def flickr_query(self, page):
        """A method for querying flickr API
        
        Queries are based on the current params of the main loop. In case of
        an error, a query is retried a maximum of 5 times. Returns only the
        photos from the result.
        """

        # TODO: What to do in the hypothetical case that a query fails all
        # attempts, i.e. a bbox would be left empty?
        for attempt in range(5):
            try:
                # Query flickr
                result = self.flickr.photos.search(
                    per_page=250,               # Geo-query limit is 250
                    has_geo=1,                  # Photos with geolocation
                    min_taken_date=f"{self.min_date_str}",
                    max_taken_date=f"{self.max_date_str}",
                    bbox=(
                        f"{self.bbox[0]}, {self.bbox[1]}, "
                        f"{self.bbox[2]}, {self.bbox[3]}"
                    ),
                    media="photos",             # Photos only
                    sort="date-taken-desc",     # Photos from latest
                    privacy_filter=1,           # Public photos
                    safe_search=1,              # photos without violence
                    extras="geo, url_n, date_taken, views, license",
                    page=page,
                )
            except FlickrError as e:
                self.logger.warn(f"Flickr API returned an error: {e}. Trying again.")
                self.q_count += 1
                continue
            break

        self.q_count += 1
        self.logger.info("    queries:", self.q_count)
        return result["photos"]


    def add_new_params(self, new_params:list):
        """A method for adding new parameters if a query returns too much data

        New parameters are added either by dividing the bounding box or the
        time extent. Time extent is divided only if the bounding box is too
        small for dividing.
        """

        self.logger.info("    Too much data, trying with new prameters")
        # Divide bbox if possible
        if (
            (self.bbox[2] - self.bbox[0] > 1e-4) and
            (self.bbox[3] - self.bbox[1] > 1e-4)
        ):
            self.logger.info("      Bbox big enough to divide, dividing bbox")
            # Divide bbox to 4, add new bboxes to new params
            middle_lon = (self.bbox[0] + self.bbox[2]) / 2
            middle_lat = (self.bbox[1] + self.bbox[3]) / 2
            new_params.append((
                (self.bbox[0],self.bbox[1],middle_lon,middle_lat),
                self.min_date, self.max_date
            ))
            new_params.append((
                (middle_lon,self.bbox[1],self.bbox[2],middle_lat),
                self.min_date, self.max_date
            ))
            new_params.append((
                (self.bbox[0],middle_lat,middle_lon,self.bbox[3]),
                self.min_date, self.max_date
            ))
            new_params.append((
                (middle_lon,middle_lat,self.bbox[2],self.bbox[3]),
                self.min_date, self.max_date
            ))

        # If bbox too small, divide time extent instead
        else:
            self.logger.info("      Bbox too small to divide, dividing time extent")
            # Divide time extent to 2, add new dates to params_list
            mid_date = self.min_date + (self.max_date - self.min_date) / 2
            new_params.append((self.bbox, self.min_date, mid_date))
            new_params.append((self.bbox, mid_date, self.max_date))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import Flickr data for given boundingbox")
    parser.add_argument("-bbox", default=None, help="Boundingbox to import")
    args = vars(parser.parse_args())
    # BBOX (minx, miny, maxx, maxy)
    bbox = args["bbox"]
    if not bbox:
        raise AssertionError("You must specify a bounding box.")
    importer = FlickrImporter(bbox=bbox)
    importer.run()