var bboxMap = L.map('bbox_map').setView([60.5, 24.2], 8);

L.tileLayer('https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}@2x.png', {
    maxZoom: 18,
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    id: 'osm',
    tileSize: 512,
    zoomOffset: -1
}).addTo(bboxMap);
var bboxFeature = new L.FeatureGroup();
var drawControlEditOnly = new L.Control.Draw({
    edit: {
        featureGroup: bboxFeature
    },
    draw: false
});
bboxMap.addControl(drawControlEditOnly);
bboxMap.addLayer(bboxFeature);