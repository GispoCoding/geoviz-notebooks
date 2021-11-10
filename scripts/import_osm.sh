#!/bin/bash

# invoke with ./import_osm.sh continent country city-slug osm_extracts_apikey
SCRIPT=`realpath $0`
SCRIPTPATH=$(dirname "$SCRIPT")
DATA_PATH="data"

# data should be stored one directory level above importers
cd $SCRIPTPATH
cd ..
mkdir $DATA_PATH
cd $DATA_PATH

echo "https://app.interline.io/osm_extracts/download_latest?string_id=$3\_$2\&data_format=pbf\&api_token=$4"

# 1) Try OSM extracts for the city first
if test -f "$3.osm.pbf"; then
    echo "OSM extract for $3 found cached, importing to PostGIS..."
elif curl --fail --location https://app.interline.io/osm_extracts/download_latest?string_id=$3\_$2\&data_format=pbf\&api_token=$4 -o $CITY.osm.pbf; then
    echo "OSM extract for $3 downloaded, importing to PostGIS..."
# 2) Fallback: download the whole country
elif test -f "$2.osm.pbf"; then
    echo "OSM extract for $3 not found, importing the whole country."
    echo "OSM extract for $2 found cached, importing to PostGIS..."
elif curl --fail http://download.geofabrik.de/$1/$2-latest.osm.pbf -o $2.osm.pbf; then
    echo "OSM extract for $3 not found, downloading the whole country."
    echo "OSM extract for $2 downloaded, importing to PostGIS..."
else
    echo "No OSM data found in $1 with country name $2"
    exit 1
fi

if test -f "$3.osm.pbf"; then
    INPUT_FILE=$3.osm.pbf
else
    INPUT_FILE=$2.osm.pbf
fi

# now injecting the variable schema name to osm2pgsql config is ugly
sed "s/city_specific_schema/$3/" $SCRIPTPATH/flex-config/generic.lua > config.lua.tmp
osm2pgsql -d geoviz -O flex $INPUT_FILE -S config.lua.tmp --slim

# Finally, osm2pgsql saves polygons and points in separate tables. Do some postprocessing to get
# all data we want in point table
echo "Postprocessing OSM tables..."
# add primary key to prevent duplicate imports
psql -d geoviz -c "alter table $3.osmpoints add primary key (node_id);"
# add polygon centroids as points; only add points not existing yet
psql -d geoviz -c "insert into $3.osmpoints (
    select -area_id as node_id, tags, st_centroid(geom) as geom from $3.osmpolygons
) on conflict (node_id) do nothing;"