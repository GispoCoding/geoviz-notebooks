from models import OSMPoint, FlickrPoint, GTFSStop, OSMAccessNode, OoklaPoint, KonturPoint

DATASETS = {
    'osm': {
        'label': 'OpenStreetMap amenities',
        'model': OSMPoint,
        'name': 'places',
        'weight': 1
    },
    'flickr': {
        'label': 'Flickr images',
        'model': FlickrPoint,
        'name': 'photographers',
        'group_by': 'properties.owner',
        'weight': 1
    },
    'gtfs': {
        'label': 'GTFS transit stops',
        'model': GTFSStop,
        'name': 'trips',
        'plot': 'sum',
        'column': 'properties.ntrips',
        'weight': 1
    },
    'access': {
        'label': 'OpenStreetMap walking times',
        'model': OSMAccessNode,
        'name': 'access',
        'plot': 'mean',
        'column': 'accessibilities.5',
        'weight': -1
    },
    'ookla': {
        'label': 'Ookla Internet device numbers',
        'model': OoklaPoint,
        'name': 'devices',
        'plot': 'sum',
        'column': 'properties.devices',
        'weight': 1
    },
    'kontur': {
        'label': 'Kontur population density',
        'model': KonturPoint,
        'name': 'population',
        'plot': 'sum',
        'column': 'properties.population',
        'weight': 1
    }
}
