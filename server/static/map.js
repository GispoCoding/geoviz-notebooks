if (document.getElementById('bbox_map')) {
    var bboxMap = L.map('bbox_map', {editable: true}).setView([60.5, 24.2], 8);
    L.control.scale({maxWidth: 200, imperial: false}).addTo(bboxMap);

    L.tileLayer(tilesUrl, {
        maxZoom: 18,
        attribution: 'Map <a href="https://memomaps.de/">memomaps.de</a> <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        id: 'osm'
    }).addTo(bboxMap);

    // editable layer
    var bboxFeature = new L.FeatureGroup();
    bboxMap.addLayer(bboxFeature);

    function setBbox(bbox) {
        document.getElementById('bbox-bbox').value = bbox.join();
        bounds = [[bbox[1], bbox[0]], [bbox[3], bbox[2]]];
        // clear old bbox
        bboxFeature.clearLayers();
        L.rectangle(bounds, {color: "#ff7800", weight: 1}).addTo(bboxFeature);
        // make new bbox editable
        bboxFeature.getLayers()[0].enableEdit();
        bboxMap.fitBounds(bounds);
        checkBbox(bbox);
    }

    // TODO: convert this to allow drawing a new bbox without selecting a city first?
    // event handlers
    // Disable finding bbox by clicking. Will interfere with actually editing the bbox.
    // bboxMap.on("click", e => {
    //     // look for closest bbox
    //     url = osmnamesUrl + 'r/boundary/' + e.latlng.lng + '/' + e.latlng.lat + '.js';
    //     fetch(url)
    //         .then(response => response.json())
    //         .then(data => {
    //             city = data.results[0];
    //             setBbox(city.boundingbox);
    //             document.getElementById('bbox-city').value = city.name;
    //         });
    // });
    bboxMap.on("editable:editing", e => {
        bboxString = bboxFeature.getBounds().toBBoxString();
        document.getElementById('bbox-bbox').value = bboxString;
        checkBbox(bboxString.split(","));
    });
};