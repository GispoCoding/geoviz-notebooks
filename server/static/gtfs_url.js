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
                document.getElementById('gtfs_urls-0').value = data.url;
            } else {
                document.getElementById('gtfs_urls-0').value = '';
            };
        });
    checkGtfsUrls();
};

var gtfsForm = document.getElementById('gtfs_url_form')
const addButton = document.getElementById('gtfs_url_row_add')
const removeButton = document.getElementById('gtfs_url_row_remove')

function getRowNumber() {
    return document.querySelectorAll("[id^='gtfs_urls-']").length
}

function addRow() {
    rows = getRowNumber()
    id = 'gtfs_urls-' + rows
    row = document.createElement('input')
    row.setAttribute("id", id)
    row.setAttribute("name", id)
    gtfsForm.insertBefore(row, gtfsForm.children[rows + 1])
    removeButton.disabled = false
    if (rows > 9) {
        addButton.disabled = true
    }
    row.addEventListener('input', () => {checkGtfsUrls()})
}

function removeRow() {
    rows = getRowNumber()
    id = 'gtfs_urls-' + (rows - 1)
    row = document.getElementById(id)
    gtfsForm.removeChild(row)
    if (rows < 3) {
        removeButton.disabled = true
    }
    addButton.disabled = false
}

addButton.addEventListener('click', () => {addRow()})
removeButton.addEventListener('click', () => {removeRow()})
