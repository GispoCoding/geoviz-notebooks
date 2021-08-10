# geoviz-notebooks

## Requirements

* Python >= 3.8
* [Osm2pgsql](https://osm2pgsql.org/doc/install.html)
* PostGIS accepting connections at localhost:5432

## How to get started

We recommend creating your own conda env, pyenv, or pyenv which contains conda wheels.
The last option should make installing all dependencies easier:

```
pyenv install miniconda-latest
pyenv local miniconda-latest
pip install -r requirements.txt
```

If you wish to import data from the Flickr API, fill in your Flickr api key and secret
in the `.env` file or the corresponding environment variable.

Then, you may import all datasets for any city with a single command

```
python ./import.py Helsinki
```

or any other city. You may also import single datasets by separately running any of the scripts
inside the scripts directory.

Do note that cities in bigger countries will be slower to import, since currently we download
the OSM data for the entire country. All other dataset sizes are determined by the size of the city.

If the city you want to import does not have a GTFS feed URL in `scripts/import_gtfs.py`
`GTFS_DATASETS` variable, you may add the right URL manually there (please make a PR too), or
alternatively run the import with the right URL as parameter, e.g.

```
python ./import.py Tallinn --gtfs https://transitfeeds.com/p/maanteeamet/510/latest/download
```
