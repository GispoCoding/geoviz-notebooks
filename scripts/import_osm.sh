# invoke with ./import_osm.sh europe finland
SCRIPT=`realpath $0`
SCRIPTPATH=$(dirname "$SCRIPT")
createdb geoviz
if test -f "$2.osm.pbf"; then
    echo "OSM extract for $2 found cached, importing to PostGIS..."
elif curl --fail http://download.geofabrik.de/$1/$2-latest.osm.pbf > $2.osm.pbf; then
    echo "OSM extract for $2 downloaded, importing to PostGIS..."
else
    echo "No OSM data found in $1 with country name $2"
    exit 1
fi
osm2pgsql -d geoviz -O flex $2.osm.pbf -S $SCRIPTPATH/flex-config/generic.lua --slim
