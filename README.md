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

If you wish to import data from the Flickr API, fill in your
[Flickr api key](https://www.flickr.com/services/api/misc.api_keys.html) and secret
in the `.env` file or the corresponding environment variable.

If you wish to import OSM data faster by using city-specific
[OSM extracts](https://www.interline.io/osm/extracts/), fill in your
[OSM extracts api key](https://app.interline.io/products/osm_extracts/orders/new)
in the `.env` file or the corresponding environment variable.

---

Then, you may import all datasets for any city with a single command

```
python ./import.py Helsinki
```

or any other city. You may import multiple cities in the same database if you wish to do
comparisons between cities. You may also import single datasets by separately running any of
the scripts inside the scripts directory.

Do note that cities in bigger countries may be slow to import if the city is not available
as a separate OSM extract. In that case, we will have to download the whole country. All other
dataset sizes are determined by the size of the city.

If a city you want to import does not have a GTFS feed URL in `scripts/import_gtfs.py`
`GTFS_DATASETS` variable, you may add the right URL manually there (please make a PR too), or
alternatively run the import with the right URL as parameter, e.g.

```
python ./import.py Tallinn --gtfs https://transitfeeds.com/p/maanteeamet/510/latest/download
```
