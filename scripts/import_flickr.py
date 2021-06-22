import calendar
import os
import sys
import time
from flickrapi import FlickrAPI, FlickrError
from dotenv import load_dotenv
from ipygis import get_connection_url
from shapely.geometry import Point
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from geoalchemy2.shape import from_shape


# save api key to env variable if found
load_dotenv()

# test simple import now, convert to module later
sys.path.insert(0, "..")
from models import FlickrPoint

sql_url = get_connection_url(dbname="geoviz")
engine = create_engine(sql_url)
session = sessionmaker(bind=engine)()
FlickrPoint.__table__.create(engine, checkfirst=True)

flickr_api_key = os.getenv("FLICKR_API_KEY")
flickr_secret = os.getenv("FLICKR_SECRET")

# BBOX (minx, miny, maxx, maxy)
city = 'HEL'

if city == 'COP':
    total_bbox = '12.42000, 55.61000, 12.65000, 55.78000'
    
elif city == 'HEL':
    total_bbox = '24.82345, 60.14084, 25.06404, 60.29496'
    
elif city == 'WAR':
    total_bbox = '20.79057, 52.09901, 21.31300, 52.38502'

# Output fp
output_json = 'flickr_'+city+'_daily_'

# List for photos
photos = []

# List for years
years_list = list(range(2017, 2022))

# Count queries
q_count = 1

# Loop years
for year in years_list:
    
    print('\nyear: '+str(year))
    
    # Whole years
    if year < 2021:
        months_list = list(range(1,13))
    
    # Cut off current year to limit empty queries
    else:
        months_list = list(range(1,6))
    
    # Loop months
    for month in months_list:
        
        print('  month: '+str(month))
        
        # Number of days in month being looped
        n_days = calendar.monthrange(year, month)[1]
        
        # Days as a list
        days_list = list(range(1, n_days+1))
        
        # Loop days
        for day in days_list:
            
            print('    day: '+str(day))
            
            # Get min and max timestamps (mysql format)
            min_taken_date = str(year) + '-' + str(month) + '-' + str(day) + ' 00:00:00'
            max_taken_date = str(year) + '-' + str(month) + '-' + str(day) + ' 23:59:59'

            # Connect to Flickr
            flickr = FlickrAPI(flickr_api_key, flickr_secret, format='parsed-json')

            page = 1            
            # While loop to generate requests
            while True:
                # Protect api key (limit amount of queries)
                if q_count > 3500:
                    raise AssertionError("Over 3500 queries done! Stopping to protect API key.")
                print('      query: '+str(q_count))

                # Wait time to avoid errors
                time.sleep(0.1)

                try:
                    result = flickr.photos.search(
                        per_page = 400,             # Number of data per page
                        has_geo = 1,                # Get photos with geolocation
                        min_taken_date = min_taken_date, 
                        max_taken_date = max_taken_date,
                        bbox = total_bbox,          # Specify geographical extent
                        media = 'photos',           # Photos without video
                        sort = 'date-taken-desc',   # Photos from latest
                        privacy_filter =1,          # Public photos
                        safe_search = 1,            # photos without violence
                        extras = 'geo,url_n, date_taken, views, license',
                        page = page
                    )
                except FlickrError as e:
                    print(f"      Flickr API returned an error: {e}. Trying next request.")
                    q_count += 1
                    break

                q_count += 1

                # Add result
                photos_to_add = result['photos']
                print('        total_photos:', photos_to_add['total'])
                print('        current_pages:', page)
                photos += photos_to_add['photo']

                # Check for query size limit (10 x 400 = 4000)
                if page > 10 :
                    print("      Query has exceeded the limit of 4000 photos")
                    break
                # Break when done
                elif page >= photos_to_add['pages']:
                    break
                page += 1


flickr_points = {}
print(f"Found {len(photos)} flickr photos, importing...")
for point in photos:
    pid = point.pop("id")
    geom = from_shape(Point(float(point.pop("longitude")), float(point.pop("latitude"))), srid=4326)
    # use dict, since the json may contain the same image twice!
    if pid in flickr_points:
        print(f"Image {pid} found twice, overwriting")
    flickr_points[pid] = FlickrPoint(point_id=pid, properties=point, geom=geom)
print(f"Saving {len(flickr_points)} flickr points...")
session.bulk_save_objects(flickr_points.values())
session.commit()
