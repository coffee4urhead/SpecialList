import getCookie from "../utils.js";

function setupCommentModal(serviceId = null) {
    const overlay = document.querySelector('.modal-overlay');
    const form = document.getElementById('leave-comment-form');
    if (!overlay || !form) return;

    overlay.addEventListener('click', e => {
        if (e.target.classList.contains('modal-overlay') || e.target.classList.contains('close-modal')) {
            overlay.remove();
        }
    });

    form.addEventListener('submit', async e => {
        e.preventDefault();
        const submitButton = form.querySelector('[type="submit"]');
        submitButton.disabled = true;
        document.querySelectorAll('.error').forEach(el => el.remove());

        const formData = new FormData(form);

        try {
            const response = await fetch(`/services/${serviceId}/comment/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();

            if (data.status === 'success') {
                overlay.remove();
                console.log("Comment posted");
                window.location.reload();  // reload instead of redirect_url
            } else {
                Object.entries(data.errors).forEach(([field, errors]) => {
                    const errorElement = document.createElement('div');
                    errorElement.className = 'error';
                    errorElement.textContent = Array.isArray(errors)
                        ? errors.map(e => e.message || e).join(', ')
                        : errors;
                    const fieldElement = form.querySelector(`[name="${field}"]`);
                    if (fieldElement) fieldElement.parentNode.appendChild(errorElement);
                });
            }
        } catch (error) {
            console.error('Error submitting form:', error);
            const errorElement = document.createElement('div');
            errorElement.className = 'error';
            errorElement.textContent = 'Error submitting form. Please try again.';
            form.prepend(errorElement);
        } finally {
            submitButton.disabled = false;
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.comment-button').forEach(button => {
        button.addEventListener('click', async () => {
            const serviceId = button.dataset.serviceId;

            try {
                const response = await fetch(`/services/${serviceId}/comment/`, {
                    method: 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                if (!response.ok) throw new Error('Failed to load comment modal');

                const modalHTML = await response.text();
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = modalHTML;

                const modalOverlay = tempDiv.querySelector('.modal-overlay');
                if (modalOverlay) {
                    modalOverlay.style.display = 'block';
                    document.body.appendChild(modalOverlay);
                    setupCommentModal(serviceId);  // make form interactive
                }
            } catch (err) {
                console.error('Error loading comment modal:', err);
            }
        });
    });


    document.querySelectorAll('#comments-section form, #leave-comment-form').forEach(form => {
        form.addEventListener('submit', async e => {
            e.preventDefault();
            const submitButton = form.querySelector('[type="submit"]');
            submitButton.disabled = true;

            const actionUrl = form.action;
            const formData = new FormData(form);

            const commentId = form.closest('.reply-form-container')?.id.replace('reply-form-', '');
            if (commentId) formData.append('parent_id', commentId);

            try {
                const response = await fetch(actionUrl, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: formData
                });

                const data = await response.json();

                if (data.status === 'success') {
                    if (form.id === 'leave-comment-form') {
                        const overlay = document.querySelector('.modal-overlay');
                        if (overlay) overlay.remove();
                    }

                    if (commentId) {
                        const replyForm = document.getElementById(`reply-form-${commentId}`);
                        if (replyForm) replyForm.style.display = 'none';
                    }

                    window.location.reload();
                } else {
                    console.error('Submission error:', data.errors);
                    alert('Error submitting comment: ' + (data.message || 'Unknown error'));
                }
            } catch (error) {
                console.error('Network error:', error);
                alert('Network error submitting comment');
            } finally {
                submitButton.disabled = false;
            }
        });
    });
});
