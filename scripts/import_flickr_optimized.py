import os
import datetime
from dotenv import load_dotenv
from flickrapi import FlickrAPI
from flickrapi.exceptions import FlickrError

# For testing
import json
import pandas as pd
from io import StringIO


class FlickrImporter:
    def __init__(self, total_bbox:list, n_days:int):
        """Sets the spatial and temporal extents, connects to flickr
        
        Input parameters:
            total_bbox: The total extent of the area of interest. Format:
                        [minx:float, miny:float, maxx:float, maxy:float]
            n_days:     From how many days should photos be downloaded. Starts
                        from n days in the past, ends on today.
        """

        # Set temporal extent
        end_date = datetime.datetime.today()
        start_date = end_date - datetime.timedelta(days=n_days)

        # List for api request parameter tuples
        self.params_list = [(total_bbox, start_date, end_date)]
        
        # Connect to flickr
        load_dotenv()
        self.flickr = FlickrAPI(
            os.getenv("FLICKR_API_KEY"),
            os.getenv("FLICKR_SECRET"),
            format="parsed-json"
        )
        
        # list for photos
        self.photos = []
        # Keep track of used parameter combos and amount of queries
        self.used_params = []
        self.q_count = 0


    def run(self):
        """The main download loop
        
        Loops through the API request parameters in self.params_list, sends
        API queries and and fills self.params_list with new parameters as
        needed.
        """

        for params in self.params_list:
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
            print(f"\nbbox: {self.bbox}")
            print(f"  From: {self.min_date_str}")
            print(f"  To:   {self.max_date_str}")
    
            # A failsafe
            if params in self.used_params:
                print("Params already used, stuck in a loop -> Breaking")
                break
            self.used_params.append(params)
    
            # Start reading photos from page 1
            page = 1
            # Get photos
            while True:
                # Flickr's query limit
                if self.q_count > 3600:
                    print("query limit")
                    break

                # Query flickr
                photos_to_add = self.flickr_query(page)
        
                # If the query reaches the limit of 4000 photos (16*250=4000):
                if photos_to_add["pages"] > 16:
                    # Add new params and try again (split bbox or time extent)
                    self.add_new_params()
                    break

                # The query is small enough to download -> add photos    
                self.photos += photos_to_add["photo"]
                # Stop when photos from every page have been added
                if page >= photos_to_add["pages"]:
                    print(f"    {photos_to_add['total']} photos added")
                    break
                
                page += 1

        # TODO: Currently just saves json to csv for testing
        print(f"\n\nSaving {len(self.photos)} photos to csv")
        d = json.dumps(self.photos, sort_keys=True, indent=2)
        df = pd.read_json(StringIO(d))
        #df.to_csv("flickr_test.csv", encoding="utf-8")

    
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
                    per_page=250,               # Number of photos per page
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
                print(f"Flickr API returned an error: {e}. Trying again.")
                self.q_count += 1
                continue
            break

        self.q_count += 1
        print("    queries:", self.q_count)
        return result["photos"]
 

    def add_new_params(self):
        """A method for adding new parameters if a query returns too much data

        New parameters are added either by dividing the bounding box or the
        time extent. Time extent is divided only if the bounding box is too
        small for dividing.
        """

        print("    Too much data, trying with new prameters")
        # Divide bbox if possible
        if (
            (self.bbox[2] - self.bbox[0] > 1e-4) and
            (self.bbox[3] - self.bbox[1] > 1e-4)
        ):
            print("      Bbox big enough to divide, dividing bbox")
            # Divide bbox to 4, add new bboxes to params_list
            middle_lon = (self.bbox[0] + self.bbox[2]) / 2
            middle_lat = (self.bbox[1] + self.bbox[3]) / 2
            self.params_list.append((
                [self.bbox[0],self.bbox[1],middle_lon,middle_lat],
                self.min_date, self.max_date
            ))
            self.params_list.append((
                [middle_lon,self.bbox[1],self.bbox[2],middle_lat],
                self.min_date, self.max_date
            ))
            self.params_list.append((
                [self.bbox[0],middle_lat,middle_lon,self.bbox[3]],
                self.min_date, self.max_date
            ))
            self.params_list.append((
                [middle_lon,middle_lat,self.bbox[2],self.bbox[3]],
                self.min_date, self.max_date
            ))
            
        # If bbox too small, divide time extent instead
        else:
            print("      Bbox too small to divide, dividing time extent")
            # Divide time extent to 2, add new dates to params_list
            mid_date = self.min_date + (self.max_date - self.min_date) / 2
            self.params_list.append((self.bbox, self.min_date, mid_date))
            self.params_list.append((self.bbox, mid_date, self.max_date))
        

# TODO: Currently just does a test import
if __name__ == "__main__":

    # Track time
    import_start_time = datetime.datetime.now()
    
    # Example params
    # bbox: [minx, miny, maxx, maxy]
    hki_bbox = [24.82345, 60.14084, 25.06404, 60.29496]
    # From how many days should photos be downloaded
    n_days = 365 * 2

    # Download photos
    importer = FlickrImporter(total_bbox=hki_bbox, n_days=n_days)
    importer.run()

    # How long it took
    print(f"Total import time: {datetime.datetime.now() - import_start_time}")