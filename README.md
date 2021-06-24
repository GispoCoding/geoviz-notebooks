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

Then, you may import all datasets for any city with a single command

```
python ./import.py Helsinki
```

or any other city. You may also import single datasets by separately running any of the scripts
inside the scripts directory.

Do note that cities in bigger countries will be slower to import, since currently we download
the OSM data for the entire country. All other dataset sizes are determined by the size of the city.

Also, GTFS dataset location will have to be added manually in `scripts/import_gtfs.py`
`GTFS_DATASETS` variable, if you need GTFS datasets from cities other than Helsinki, Copenhagen
or Warsaw. Feel free to make a PR to add lots of fancy GTFS URLs there!
