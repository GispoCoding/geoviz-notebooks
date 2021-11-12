const deleteButtons = document.querySelectorAll('.cancel-button');
const spinners = document.querySelectorAll('.cancel-button-spinner');
const modalElements = document.querySelectorAll("[id^='modal_cancel']");
const verifyDeletes = document.querySelectorAll("[id^='button_cancel'][id$='yes']");
const verifyDeleteSpinners = document.querySelectorAll("[id^='button_cancel'][id$='yes_spinner']");
const cancelDeletes = document.querySelectorAll("[id^='button_cancel'][id$='no']");
M.Modal.init(modalElements, {dismissible: false});
console.log(verifyDeletes)
console.log(verifyDeleteSpinners)

if (deleteButtons) {
    deleteButtons.forEach((element, index) => {
        element.addEventListener('click', (e) => {
            element.disabled = true;
            const spinner = spinners[index];
            spinner.classList.add('active');
            const slug = /^delete_([-a-z0-9]+)$/.exec(element.id)[1]
            const modalElement = document.getElementById('modal_cancel_' + slug)
            var modal = M.Modal.getInstance(modalElement);
            modal.open();
        });
    });
    verifyDeletes.forEach((element, index) => {
        element.addEventListener('click', (e) => {
            element.disabled = true;
            cancelDeletes[index].disabled = true;
            verifyDeleteSpinners[index].classList.add('active');
            const slug = /^button_cancel_([-a-z0-9]+)_yes$/.exec(element.id)[1]
            url = '/analyses/' + slug;
            fetch(url, {method: 'DELETE'})
                .then(data => {
                    location.reload();
                });
        });
    });
    cancelDeletes.forEach((element, index) => {
        element.addEventListener('click', (e) => {
            const button = deleteButtons[index];
            button.disabled = false;
            const spinner = spinners[index];
            spinner.classList.remove('active');
        });
    });
};