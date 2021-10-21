var autocomplete = new kt.OsmNamesAutocomplete(
    'city_search', 'https://geoviz.gispocoding.fi/');

autocomplete.registerCallback(function (item) {
    bbox = item.boundingbox
    document.getElementById('bbox').value = bbox.join();
    bounds = [[bbox[1], bbox[0]], [bbox[3], bbox[2]]];
    // clear old bbox
    bboxFeature.clearLayers();
    L.rectangle(bounds, {color: "#ff7800", weight: 1}).addTo(bboxFeature);
    // make new bbox editable
    bboxFeature.getLayers()[0].enableEdit();
    bboxMap.fitBounds(bounds);
}, true);