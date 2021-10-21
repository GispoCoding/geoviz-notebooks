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

function setBbox(bbox) {
    document.getElementById('bbox').value = bbox.join();
    bounds = [[bbox[1], bbox[0]], [bbox[3], bbox[2]]];
    // clear old bbox
    bboxFeature.clearLayers();
    L.rectangle(bounds, {color: "#ff7800", weight: 1}).addTo(bboxFeature);
    // make new bbox editable
    bboxFeature.getLayers()[0].enableEdit();
    bboxMap.fitBounds(bounds);
}

// event handlers
bboxMap.on("click", e => {
    // look for closest bbox
    url = osmnamesUrl + 'r/boundary/' + e.latlng.lng + '/' + e.latlng.lat + '.js'
    fetch(url)
        .then(response => response.json())
        .then(data => {
            city = data.results[0]
            setBbox(city.boundingbox)
            document.getElementById('city_search').value = city.name
        });
});
bboxMap.on("editable:editing", e => {
    document.getElementById('bbox').value = bboxFeature.getBounds().toBBoxString();
});