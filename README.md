# geoviz-notebooks
<img width="913" alt="image" src="https://user-images.githubusercontent.com/9367712/130978610-dc3a6a7c-ed78-47c4-b380-fcd1b354126c.png">
<img width="913" alt="image" src="https://user-images.githubusercontent.com/9367712/141969037-ae9674db-0037-48d7-b4f8-173929b73278.png">

Python tool for analyzing geospatial data in cities.

This repo consists of three components that can be run separately or together:
- [*https server and UI*](#how-to-use-the-ui) that allow running the whole analysis process
automatically and browsing the result maps from the comfort of your favorite web browser
- [*import scripts*](#importing) that import a variety of open geospatial datasets for your favorite city
- [*notebook or export script*](#running-analysis-notebook-and-creating-result-map) that
  - combine the datasets to form an index value per [H3 hex](https://github.com/uber/h3), and
  - create a [Kepler.gl](https://github.com/keplergl/kepler.gl) H3 map of the index

It is recommended to use the UI, if you want to just get a fancy map, but you may run the
scripts and notebook manually if you want more control in what is included in your analysis.

## Requirements

* Docker
* Docker-compose

OR

* Python >= 3.8
* [Osm2pgsql](https://osm2pgsql.org/doc/install.html)
* PostGIS accepting connections at localhost:5432

## How to get started with docker

If you wish to run the UI to run analyses with a few clicks, you may start the
database and development server locally by typing
```
docker-compose up dev
```
Set up the needed username and password as in [configuration](#configuration).

If you wish to run the analysis notebook manually, you will get the database and
notebook up by typing
```
docker-compose up notebook
```

The https production server can be started by
```
cp server/flask.subdomain.conf server/swag/nginx/proxy-confs/
docker-compose up serve
```
Do note that the server requires a domain you must register to get a https certificate.
Look at [configuration](#configuration) for details.


## How to get started without docker

If you're *not* running docker, we recommend creating your own conda env, pyenv, or pyenv
which contains conda wheels. The last option should make installing all dependencies easier:

```
pyenv install miniconda3-latest
pyenv local miniconda3-latest
pip install -r requirements.txt
```

You also need to have PostGIS running. To run the Flask dev server and UI locally, after
installing the basic requirements,
```
cd server
pip install -r requirements-serve.txt
flask run
```

Or, if you want to use the notebook instead of the UI, start the notebook server by

```
jupyter notebook
```

## Configuration

Configuration is by the `.env` file or environment variables. You may copy
[.env.example](.env.example) to a file called `.env` and fill in your secrets.

To use the UI, set the username and password that allows access to the UI by setting
the desired username and password hash in `.env` file or the corresponding environment variable.

If you wish to import data from the Flickr API, fill in your
[Flickr api key](https://www.flickr.com/services/api/misc.api_keys.html) and secret
in a `.env` file or the corresponding environment variable. The API key may also be set in 
the UI for each import run, but it will not persist to the server environment.

To get https certificates on AWS EC2, you need to add your own domain and subdomain in `.env` and your
AWS access credentials in `server/swag/dns-conf/route53.ini`. If you use MFA, you have to
create a separate non-MFA-role specific to your EC2 instance and instead add `role_arn` and
`credential_source=Ec2InstanceMetadata` in `route53.ini` just like in [AWS Config file](https://docs.aws.amazon.com/cli/latest/topic/config-vars.html#using-aws-iam-roles). This will allow [Swag](https://docs.linuxserver.io/general/swag) to automatically
retrieve and update your certificate. If you are running on a provider other than AWS,
read [Swag instructions](https://docs.linuxserver.io/general/swag#create-container-via-dns-validation-with-a-wildcard-cert) and change DNSPLUGIN value at [docker-compose.yml#L20].

## How to use the UI

Please, [add your API keys and username/password hash in the configuration](#configuration) first.
Then, start your local dev server at http://localhost:5000 by
```
docker-compose up dev    # if you are running docker
cd server & flask run    # if you are not running docker
```

or your https server at https://yourdomain.com:443 by
```
cp server/flask.subdomain.conf server/swag/nginx/proxy-confs/
docker-compose up serve
```
<img width="1010" alt="image" src="https://user-images.githubusercontent.com/9367712/141968692-a75dc884-7766-4101-933c-1dbde0f6089e.png">

You may import the city of your choice in the UI by
1) selecting the datasets you desire,
2) selecting your city from the autocomplete list,
3) (optionally) adjusting the bounding box on the map, if the initial bbox doesn't look suitable for you,
4) (optionally) adding a GTFS url for your city, if it is not known by the app already,
5) clicking "Import Datasets".

The process will take a while depending on how many and which datasets you are importing. Importing
small datasets such as Ookla and Kontur data is very fast, while using the Flickr API will be particularly
slow and will keep you waiting for a *long* time.

<img width="1072" alt="image" src="https://user-images.githubusercontent.com/9367712/141968862-165a9303-ddc8-479e-b668-a150b418404f.png">

You may look at how the request is processing by clicking the "View Log" button. Once the run is finished,
click "View Results" to see all your datasets and the combination total index values on the hex map. All old
import runs are listed under "Result maps".

## How to use the command line

### Importing

From the command line, you may do the import by running

```
docker-compose run notebook ./import.py Helsinki  # if you are running docker
./import.py Helsinki                               # if you are not running docker
```

or any other city. You may only import some datasets by --datasets parameter, e.g.
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

### Running analysis notebook and creating result map

The UI calculates the result map automatically if the import is started by the UI. Once the run is
finished, your map is available by clicking "View Results" next to your import run.

You may also run export automatically at the end of import by calling `./import.py` with the `--export`
parameter, or run the export script after import has finished by
```
docker-compose run notebook ./export.py  # if you are running docker
./export.py                               # if you are not running docker
```

On the other hand, you calculate the results manually using the [export notebook](notebooks/export.ipynb).
The notebook is available at localhost:8888/tree/notebooks/export.ipynb .

Open the notebook to adjust
- the datasets you wish to include
- the column/sum/mean value you wish to use from each dataset
- the weight of each dataset in the result map

You may just run the notebook as-is to get the default index that contains representative
columns/statistics from each dataset, with equal weights for each dataset. This is the same
setup that the export script uses for calculating the results. The resulting map is displayed
in the notebook and saved as a standalone HTML map in server/maps/city_name.html.
