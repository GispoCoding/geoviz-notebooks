from sqlalchemy import or_

from models import OSMPoint

# This file contains the OSM tags we want to consider as amenities.
# Edit this file to change OSM density and accessibility analysis.
# The same tag set is used for *both* OSM amenity density layer
# *and* OSM amenity accessibility layer.
#
# We want to consider all "third places", i.e. public places where
# people regularly gather or visit in their daily life.
#
# List the tag values you want to consider, or True to allow all
# values.

tags_to_filter = {
    # https://wiki.openstreetmap.org/wiki/Key:amenity
    # Added cultural amenities so we don't only focus on food
    "amenity": [
        "restaurant",
        "bar",
        "pub",
        "biergarten",
        "cafe",
        "food",
        "marketplace",
        "fast_food",
        "food_court",
        "ice_cream",
        "arts_centre",
        "cinema",
        "club",
        "community_centre",
        "library",
        "nightclub",
        "theatre",
        "place_of_worship",
        "public_bath"
        ],
    # https://wiki.openstreetmap.org/wiki/Key:shop
    # Due to the variety of tags, consider all shops regardless of article.
    # A list of shops for daily needs is too exhaustive to implement.
    "shop": True,
    # https://wiki.openstreetmap.org/wiki/Key:leisure
    # Outdoor and sports activities are under this tag
    "leisure": [
        "park",
        "pitch",
        "playground",
        "fitness_centre",
        "fitness_station",
        "sports_centre",
        "sports_hall",
        "swimming_area",
        "swimming_pool",
        "sauna"
        ],
    # https://wiki.openstreetmap.org/wiki/Key:tourism
    # Some cultural amenities are marked "tourism" even though
    # locals use them too.
    "tourism": [
        "museum",
        "gallery",
        "picnic_site"
        ]
}

# SQLAlchemy needs a bit more involved syntax to filter by value of JSONB key
# https://docs.sqlalchemy.org/en/14/dialects/postgresql.html#sqlalchemy.dialects.postgresql.JSONB
# TODO: fix this filter to allow osmpoints *as well as* osmpolygons
tag_filter = or_(*[(
    OSMPoint.tags[tag].astext.in_(values) if isinstance(values, list)
    else OSMPoint.tags.has_key(tag)
    ) for tag, values in tags_to_filter.items()])
