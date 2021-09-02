# geoviz-notebooks
<img width="913" alt="image" src="https://user-images.githubusercontent.com/9367712/130978610-dc3a6a7c-ed78-47c4-b380-fcd1b354126c.png">

Python tool for analyzing geospatial data in cities.

This repo consists of three components:
- [*import scripts*](#how-to-import-data) that import a variety of open geospatial datasets for your favorite city
- [*notebook or export script*](#how-to-create-result-map) that
  - combine the datasets to form an index value per [H3 hex](https://github.com/uber/h3), and
  - create a [Kepler.gl](https://github.com/keplergl/kepler.gl) H3 map of the index
- [*https server*](#how-to-share-the-map) that serves the resulting map password protected if the notebook is run on a server

## Requirements

* Docker
* Docker-compose

OR

* Python >= 3.8
* [Osm2pgsql](https://osm2pgsql.org/doc/install.html)
* PostGIS accepting connections at localhost:5432

## How to get started

If you wish to use the ready made docker compose file, you will get the database and
notebook up by typing

```
docker-compose up notebook
```

### How to get started without docker

If you're *not* running docker, we recommend creating your own conda env, pyenv, or pyenv
which contains conda wheels. The last option should make installing all dependencies easier:

```
pyenv install miniconda-latest
pyenv local miniconda-latest
pip install -r requirements.txt
```

You also need to have PostGIS running. Then you may start the notebook server by

```
jupyter notebook
```

## Configuration

If you wish to import data from the Flickr API, fill in your
[Flickr api key](https://www.flickr.com/services/api/misc.api_keys.html) and secret
in the `.env` file or the corresponding environment variable.

If you wish to import OSM data faster by using city-specific
[OSM extracts](https://www.interline.io/osm/extracts/), fill in your
[OSM extracts api key](https://app.interline.io/products/osm_extracts/orders/new)
in the `.env` file or the corresponding environment variable.

## How to import data

Please, [add your API keys in the configuration](#configuration) first. Then,
you may import all datasets for any city with a single command

```
docker-compose run notebook ./import.py Helsinki  # if you are running docker
./import.py Helsinki                               # if you are not running docker
```

or any other city. You may import multiple cities in the same database if you wish to do
comparisons between cities. You may only import some datasets by --datasets parameter, e.g.
`./import.py Helsinki --datasets "access gtfs ookla"`.

Do note that cities in bigger countries may be slow to import if the city is not available
as a separate OSM extract. In that case, we will have to download the whole country. All other
dataset sizes are determined by the size of the city.

If a city you want to import does not have a GTFS feed URL in [scripts/import_gtfs.py](scripts/import_gtfs.py)
`GTFS_DATASETS` variable, you may add the right URL manually there (please make a PR too), or
alternatively run the import with the right URL as parameter, e.g.

```
./import.py Tallinn --gtfs http://www.peatus.ee/gtfs/gtfs.zip
```

## How to create result map

Once you have all the datasets imported for your desired city/cities, it is time to calculate
the desired combination index on the H3 hex grid.

The index is calculated by the [export notebook](notebooks/export.ipynb). The notebook is
available at localhost:8888/tree/notebooks/export.ipynb .

Open the notebook to adjust
- the datasets you wish to include
- the column/sum/mean value you wish to use from each dataset
- the weight of each dataset in the result map

You may just run the notebook as-is to get the default index that contains representative
columns/statistics from each dataset, with equal weights for each dataset. The resulting map is displayed
in the notebook and saved as a standalone HTML map in notebooks/keplergl_map.html.

To just get the result map non-interactively, you may run the notebook on the command line with

```
docker-compose run notebook ./export.sh  # if you are running docker
./export.sh                               # if you are not running docker
```

The resulting map is saved as a standalone HTML map in notebooks/keplergl_map.html so you
may share the file. Do note that the HTML file may be huge if the datasets are big.


## How to share the map

The docker configuration contains a simple https server that serves the latest keplergl_map.html
password-protected. The map is served at localhost:443/map by running

```
cp server/flask.subdomain.conf server/swag/nginx/proxy-confs/
docker-compose up serve
```

You may set the username and password that allows access to the visualization by setting the desired
username and password hash in [server/.env](server/.env). To get https certificates, you need to add
your own domain and subdomain in [docker-compose.yml#L17] and your
AWS access credentials in server/swag/dns-conf/route53.ini , or read [Swag instructions](https://docs.linuxserver.io/general/swag#create-container-via-dns-validation-with-a-wildcard-cert) and change DNSPLUGIN value at [docker-compose.yml#L20] if you are running on a provider
other than AWS.

Therefore, there are a few ways of getting your custom visualization html shared with the audience:
- change and run the notebook on your computer (or run export.sh) and distribute the resulting html file
- change and run the notebook on the server (or run export.sh) to update the map on the server
- if you wish to make the new parameters official, make a PR to this repo.
