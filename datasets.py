from models import OSMPoint, FlickrPoint, GTFSStop, OSMAccessNode, OoklaPoint, KonturPoint

# Dataset definition schema:
# 'dataset_id': {
#   'label': Text to display in analysis UI
#   'model': SQLAlchemy base to use
#   'name': Name to display in Kepler map
#   'weight': Weight in the sum (index) layer. Positive weight means layer minimum will get value zero
#        in the index and layer maximum will get value weight. Negative weight means layer maximum
#        will get value zero and layer minimum will get value abs(weight).
#   'group_by': (optional) Field to group points by before plotting. Default None.
#   'plot': (optional) Function to use when combining values within one H3 hex. Default 'size'.
#        Possible functions are https://pandas.pydata.org/docs/reference/groupby.html#computations-descriptive-stats
#   'column': (optional) Field whose value to plot. Default None will just count point numbers.
# }

DATASETS = {
    'osm': {
        'label': 'OpenStreetMap amenities',
        'model': OSMPoint,
        'name': 'Number of amenities',
        'weight': 1
    },
    'flickr': {
        'label': 'Flickr photographers',
        'model': FlickrPoint,
        'name': 'Number of photographers',
        'group_by': 'properties.owner',
        'weight': 1
    },
    'gtfs': {
        'label': 'GTFS departures',
        'model': GTFSStop,
        'name': 'Transit departures per day',
        'plot': 'sum',
        'column': 'properties.ntrips',
        'weight': 1
    },
    'access': {
        'label': 'OpenStreetMap walking times',
        'model': OSMAccessNode,
        'name': 'Walking times to five amenities',
        'plot': 'mean',
        'column': 'accessibilities.5',
        'weight': -1
    },
    'ookla': {
        'label': 'Ookla Internet device numbers',
        'model': OoklaPoint,
        'name': 'Internet device numbers',
        'plot': 'sum',
        'column': 'properties.devices',
        'weight': 1
    },
    'kontur': {
        'label': 'Kontur population density',
        'model': KonturPoint,
        'name': 'Population density',
        'plot': 'sum',
        'column': 'properties.population',
        'weight': 1
    }
}
