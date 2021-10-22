// osmnamesautocomplete.js does preventdefault on the parent form:
// https://github.com/klokantech/javascript/blob/master/src/osmnamesautocomplete.js#L193
// Bind submit again, but do not use the enter key. Enter should only work within
// autocomplete list.

const submitButton = document.getElementById('import_button');
const formElement = document.getElementById('import_form');
submitButton.addEventListener('click', (e) => {
    formElement.submit();
});