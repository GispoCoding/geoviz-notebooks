const bboxCity = document.getElementById('bbox-city')

var autoComplete = undefined
if (bboxCity) {
    // fetch the autocomplete url we should use
    fetch('/autocomplete_url')
        .then(response => {
            if (response.status == 200) {
                return response.json()
            }
            return null
        })
        .then(data => {
            // in case of something fishy, just use server url
            var autoCompleteUrl = '/'
            if (data) {
                autoCompleteUrl = data.url
            }
            // osmnamesautocomplete requires /
            if (!autoCompleteUrl.endsWith('/')) {
                autoCompleteUrl += '/'
            }
            autoComplete = new kt.OsmNamesAutocomplete(
                'bbox-city', autoCompleteUrl);
            autoComplete.registerCallback(function (item) {
                // Component callback may fire even when something else on the form is changed, go figure.
                // Probably the component overreacts to adding an element to the DOM tree.
                // Check that the user really *did* select an item from the list.
                // We don't want to override bbox and URL if the user is editing them at the moment.
                if (document.activeElement === bboxCity){
                    setBbox(item.boundingbox);
                    setGtfsUrl(item.name);
                }
            }, true);
        });
};
