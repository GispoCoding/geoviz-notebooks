function setGtfsUrl(city) {
    url = '/gtfs_url/' + city;
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data) {
                document.getElementById('gtfs_url').value = data.url;
            };
        });
};
