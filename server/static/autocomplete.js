var autocomplete = new kt.OsmNamesAutocomplete(
    'bbox-city', osmnamesUrl);

autocomplete.registerCallback(function (item) {
    setBbox(item.boundingbox);
}, true);