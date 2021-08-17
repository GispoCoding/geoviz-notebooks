# geoviz-notebooks

Python tool for analyzing geospatial data in cities.

This repo consists of two components:
- *import* scripts that import a variety of open geospatial datasets for your favorite city
- *notebook or export script* that
  - combine the datasets to form an index value per [H3 hex](https://github.com/uber/h3), and
  - create a [Kepler.gl](https://github.com/keplergl/kepler.gl) H3 map of the index

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

## How to import data

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

## How to create result map

Once you have all the datasets imported for your desired city/cities, it is time to calculate
the desired combination index on the H3 hex grid.

The index is calculated by the notebook (notebooks/export.ipynb). Open the notebook to adjust
-the datasets you wish to include
-the colum/sum/mean value you wish to use from each dataset
-the weight of each dataset in the result map

Or you may just run the notebook as-is to get the default index that contains representative
columns from each dataset, with equal weights for each dataset. The resulting map is displayed
in the notebook and saved as a standalone HTML map keplergl_map.html . Do note that the HTML
file will be huge, as the datasets are big.


