# invoke with ./import_osm.sh europe finland

createdb geoviz
if curl --fail http://download.openstreetmap.fr/extracts/$1/$2.osm.pbf > $2.osm.pbf; then
    echo "OSM extract for $2 downloaded, importing to PostGIS..."
    osm2pgsql -d geoviz -O flex $2.osm.pbf -S ./flex-config/generic.lua --slim
else
    echo "No OSM data found in $1 with country name $2"
    exit 1
fi
