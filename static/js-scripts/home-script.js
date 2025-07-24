const subscribeButtons = document.querySelectorAll('form[method=post] button.filled-web-btn');

const userType = document.body.dataset.userType;
const isAuthenticated = document.body.dataset.isAuthenticated === 'true';

function performCheck(event) {
    if (!isAuthenticated) {
        event.preventDefault();
        window.location.href = '/user/login' + window.location.pathname;
        return;
    }

    if (userType !== 'Provider') {
        event.preventDefault();

        const divError = document.createElement('div');
        divError.classList.add('alert-error', 'alert');
        divError.innerHTML = 'Only Providers can subscribe. <button onclick="this.parentElement.remove()">X</button>';
        document.body.appendChild(divError);

        setTimeout(() => {
            divError.remove();
        }, 2000);
    }
}

subscribeButtons.forEach((subButton) => {
    subButton.addEventListener('click', performCheck);
});