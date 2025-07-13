import getCookie from "../utils.js";

function setupCommentModal(serviceId = null) {
    const overlay = document.querySelector('.modal-overlay');
    const form = document.getElementById('leave-comment-form');

    if (!overlay || !form) return;

    overlay.addEventListener('click', function (e) {
        if (e.target.classList.contains('modal-overlay') || e.target.classList.contains('close-modal')) {
            overlay.remove();
        }
    });

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        document.querySelectorAll('.error').forEach(el => el.remove());

        const formData = new FormData(form);

        fetch(`/services/${serviceId}/comment/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const commentCountSpan = document.querySelector('span.comment-count');
                    commentCountSpan
                    overlay.remove();
                    window.location.reload();
                } else {
                    Object.entries(data.errors).forEach(([field, errors]) => {
                        const errorElement = document.createElement('div');
                        errorElement.className = 'error';
                        errorElement.textContent = Array.isArray(errors)
                            ? errors.map(e => e.message || e).join(', ')
                            : errors;

                        const fieldElement = form.querySelector(`[name="${field}"]`);
                        if (fieldElement) {
                            fieldElement.parentNode.appendChild(errorElement);
                        }
                    });
                }
            })
            .catch(error => {
                console.error('Error submitting form:', error);
                alert('Error submitting form. Please try again.');
            });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const commentButtons = document.querySelectorAll('button.comment-button');

    commentButtons.forEach((comButton) => {
        comButton.addEventListener('click', () => {
            const serviceId = comButton.dataset.serviceId;
            const formContainer = document.createElement('div');
            formContainer.id = `comment-form-${serviceId}`;
            document.body.appendChild(formContainer);

            fetch(`/services/${serviceId}/comment/`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.text();
                })
                .then(html => {
                    document.body.insertAdjacentHTML('beforeend', `
                        <div class="modal-overlay">
                            ${html}
                        </div>
                    `);
                    setupCommentModal(serviceId)
                })
                .catch(error => {
                    console.error('Error:', error);
                    formContainer.innerHTML = `<p>Error loading comment form: ${error.message}</p>`;
                });
        });
    });
});