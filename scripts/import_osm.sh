createdb geoviz
curl http://download.openstreetmap.fr/extracts/europe/finland.osm.pbf > finland.osm.pbf
osm2pgsql -d geoviz -O flex finland.osm.pbf -S ./flex-config/generic.lua