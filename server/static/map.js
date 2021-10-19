var bbox_map = L.map('bbox_map').setView([60.5, 24.2], 8);

L.tileLayer('https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}@2x.png', {
    maxZoom: 18,
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    id: 'osm',
    tileSize: 512,
    zoomOffset: -1
}).addTo(bbox_map);