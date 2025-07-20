// subscription cards error handler
const subscribeButtons = document.querySelectorAll('form[method=post] button.filled-web-btn');

const userType = "{{ request.user.user_type|escapejs }}";

function performCheck(event) {

    console.log('User Type:', userType);
    if (userType !== 'Provider' && userType) {
        event.preventDefault();
        const divError = document.createElement('div');
        divError.classList.add('alert-error');
        divError.classList.add('alert');
        divError.innerHTML = 'Only Providers can subscribe. <button onclick="this.parentElement.remove()">X</button>'
        document.body.appendChild(divError);

        setTimeout(() => {
            divError.remove();
        }, 2000);
    }
}

subscribeButtons.forEach((subButton) => {
    subButton.addEventListener('click', performCheck);
});