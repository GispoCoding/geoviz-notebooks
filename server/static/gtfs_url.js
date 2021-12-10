function setGtfsUrl(city) {
    url = '/gtfs_url/' + city;
    fetch(url)
        .then(response => {
            if (response.status == 404) {
                return null
            }
            return response.json()
        })
        .then(data => {
            if (data) {
                document.getElementById('gtfs_url').value = data.url;
            } else {
                document.getElementById('gtfs_url').value = '';
            };
        });
};
