const bboxCity = document.getElementById('bbox-city')

if (bboxCity) {
    var autocomplete = new kt.OsmNamesAutocomplete(
        'bbox-city', osmnamesUrl);

    autocomplete.registerCallback(function (item) {
        // Component callback may fire even when something else on the form is changed, go figure.
        // Probably the component overreacts to adding an element to the DOM tree.
        // Check that the user really *did* select an item from the list.
        // We don't want to override bbox and URL if the user is editing them at the moment.
        if (document.activeElement === bboxCity){
            setBbox(item.boundingbox);
            setGtfsUrl(item.name);
        }
    }, true);
};