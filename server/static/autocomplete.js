var autocomplete = new kt.OsmNamesAutocomplete(
    'city_search', osmnamesUrl);

autocomplete.registerCallback(function (item) {
    setBbox(item.boundingbox);
}, true);