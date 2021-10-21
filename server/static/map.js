var bboxMap = L.map('bbox_map', {editable: true}).setView([60.5, 24.2], 8);
L.control.scale({maxWidth: 200, imperial: false}).addTo(bboxMap);

L.tileLayer(tilesUrl, {
    maxZoom: 18,
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    id: 'osm',
    tileSize: 512,
    zoomOffset: -1
}).addTo(bboxMap);

// editable layer
var bboxFeature = new L.FeatureGroup();
bboxMap.addLayer(bboxFeature);

// event handler
bboxMap.on("editable:editing", e => {
    document.getElementById('bbox').value = bboxFeature.getBounds().toBBoxString();
});