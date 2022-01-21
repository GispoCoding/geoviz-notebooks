if (document.getElementById('bbox-city')) {
    var autocomplete = new kt.OsmNamesAutocomplete(
        'bbox-city', osmnamesUrl);

    autocomplete.registerCallback(function (item) {
        setBbox(item.boundingbox);
        setGtfsUrl(item.name);
    }, true);
};