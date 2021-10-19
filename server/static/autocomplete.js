var autocomplete = new kt.OsmNamesAutocomplete(
    'city_search', 'https://geoviz.gispocoding.fi/');

autocomplete.registerCallback(function(item) {
  alert(JSON.stringify(item, ' ', 5));
});