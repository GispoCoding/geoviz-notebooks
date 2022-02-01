function removeError(element, id = null) {
    if (!id) {
        id = element.id
    }
    errorBox = document.getElementById(id + "_error_box")
    if (errorBox) {
        element.removeChild(errorBox)
    }
}

function addError(element, text, id = null) {
    if (!id) {
        id = element.id
    }
    errorBox = document.createElement("div")
    errorBox.setAttribute("id", id + "_error_box")
    errorBox.setAttribute("class", "card-panel red lighten-2")
    errorText = document.createElement("span")
    errorText.setAttribute("class", "white-text")
    errorText.innerHTML = text
    errorBox.appendChild(errorText)
    element.appendChild(errorBox)
}

function checkBbox(bbox) {
    // check area to prevent import if bbox is too big
    bboxLimit = 100 * 100 * 1000 * 1000;
    bboxPolygon = turf.bboxPolygon(bbox);
    bboxArea = turf.area(bboxPolygon);
    cityForm = document.getElementById('city_selection_form');
    removeError(cityForm);
    if (bboxArea > bboxLimit) {
        addError(cityForm, "The bounding box is too large. Please select an area of less than 10 000 sq. km.");
    }
}

var datasets = document.querySelectorAll('input[name="dataset_selection"]')

function checkDatasets() {
    datasetForm = document.getElementById('dataset_selection_form')
    datasetList = [...datasets];
    selected_datasets = datasetList.filter(dataset => dataset.checked)
    removeError(datasetForm);
    if (!selected_datasets.length) {
        addError(datasetForm, "Please select at least one dataset to use.")
    }
}

datasets.forEach(dataset => {
    dataset.addEventListener('click', () => {checkDatasets()})
})

var flickrForm = document.getElementById('flickr_form')
var flickrApikeyField = document.getElementById('flickr_apikey')
var flickrSecretField = document.getElementById('flickr_secret')
var gtfsForm = document.getElementById("gtfs_url_form")
var gtfsField = document.getElementById("gtfs_urls-0")
var flickrCheckbox = document.querySelector('input[value="flickr"]')
var gtfsCheckbox = document.querySelector('input[value="gtfs"]')

function checkFlickrKeys () {
    removeError(flickrForm, "flickr_key_error")
    removeError(flickrForm, "flickr_secret_error")
    apikeyRegex = new RegExp("^[0-9a-f]{32}$")
    secretRegex = new RegExp("^[0-9a-f]{16}$")
    if (flickrCheckbox.checked && !apikeyRegex.test(flickrApikeyField.value)) {
        addError(flickrForm, "The flickr API key must have 32 digits or characters a-f.", "flickr_key_error")
    }
    if (flickrCheckbox.checked && !secretRegex.test(flickrSecretField.value)) {
        addError(flickrForm, "The flickr secret must have 16 digits or characters a-f.", "flickr_secret_error")
    }
}

function checkGtfsUrls () {
    var gtfsFields = document.querySelectorAll('input[id^="gtfs_urls-"]')
    removeError(gtfsForm)
    if (gtfsCheckbox.checked) {
        try {
            gtfsFields.forEach(
                (field) => {
                    // check URL validity
                    new URL(field.value)
                    // Check file type. Accept transitfeed download URLs too.
                    if (!field.value.endsWith(".zip") && !field.value.endsWith("download")) {
                        throw 'File must be .zip!'
                    }
                }
            )
        }
        catch (error) {
            addError(gtfsForm, "GTFS URL must point to a .zip file and cannot be empty.")
        }
    }
}

flickrApikeyField.addEventListener('input', () => {checkFlickrKeys()})
flickrSecretField.addEventListener('input', () => {checkFlickrKeys()})
flickrCheckbox.addEventListener('click', () => {checkFlickrKeys()})
gtfsField.addEventListener('input', () => {checkGtfsUrls()})
gtfsCheckbox.addEventListener('click', () => {checkGtfsUrl()})
