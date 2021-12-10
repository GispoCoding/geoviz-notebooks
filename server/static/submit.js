// osmnamesautocomplete.js does preventdefault on the parent form:
// https://github.com/klokantech/javascript/blob/master/src/osmnamesautocomplete.js#L193
// Bind submit again, but do not use the enter key. Enter should only work within
// autocomplete list.

if (document.getElementById('import_button')) {
    const submitButton = document.getElementById('import_button');
    const spinner = document.getElementById('import_button_spinner');
    const formElement = document.getElementById('import_form');
    const modalElement = document.getElementById('modal_submit');
    const verifySubmit = document.getElementById('button_submit_yes');
    const verifySpinner = document.getElementById('button_submit_yes_spinner');
    const cancelSubmit = document.getElementById('button_submit_no');
    M.Modal.init(modalElement, {dismissible: false});

    submitButton.addEventListener('click', (e) => {
        submitButton.disabled = true;
        spinner.classList.add('active');
        // check if analysis with the name exists already
        const city = document.getElementById('bbox-city').value;
        url = '/analyses/' + city;
        fetch(url)
            .then(response => {
                if (response.status == 404) {
                    return null
                }
                return response.json()
            })
            .then(data => {
                if (data) {
                    // ask if the user really wants to overwrite
                    var modal = M.Modal.getInstance(modalElement);
                    modal.open();
                } else {
                    // no analysis exists
                    formElement.submit();
                };
            });
    });
    verifySubmit.addEventListener('click', (e) => {
        verifySubmit.disabled = true;
        verifySpinner.classList.add('active');
        cancelSubmit.disabled = true;
        formElement.submit();
    });
    cancelSubmit.addEventListener('click', (e) => {
        submitButton.disabled = false;
        spinner.classList.remove('active');
    });
};