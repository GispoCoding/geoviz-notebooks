# invoke with ./import_osm.sh continent country city osm_extracts_apikey
SCRIPT=`realpath $0`
SCRIPTPATH=$(dirname "$SCRIPT")

# 1) Try OSM extracts for the city first
if test -f "$3.osm.pbf"; then
    echo "OSM extract for $3 found cached, importing to PostGIS..."
elif curl --fail --location https://app.interline.io/osm_extracts/download_latest?string_id=$3_$2\&data_format=pbf\&api_token=$4 -o $3.osm.pbf; then
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

# only create the database if missing
if createdb geoviz; then
    osm2pgsql -d geoviz -O flex $INPUT_FILE -S $SCRIPTPATH/flex-config/generic.lua --slim
else
    osm2pgsql -d geoviz -O flex $INPUT_FILE -S $SCRIPTPATH/flex-config/generic.lua --slim --append
fi