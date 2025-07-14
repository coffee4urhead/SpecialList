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
        const submitButton = form.querySelector('[type="submit"]');
        submitButton.disabled = true;

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
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    overlay.remove()
                    console.log("Comment posted")

                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    } else {
                        window.location.reload();
                    }
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
                const errorElement = document.createElement('div');
                errorElement.className = 'error';
                errorElement.textContent = 'Error submitting form. Please try again.';
                form.prepend(errorElement);
            })
            .finally(() => {
                submitButton.disabled = false;
            });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // Handle comment button clicks
    const commentButtons = document.querySelectorAll('button.comment-button');
    commentButtons.forEach((comButton) => {
        comButton.addEventListener('click', () => {
            const serviceId = comButton.dataset.serviceId;
            const existingOverlay = document.querySelector('.modal-overlay');
            if (existingOverlay) {
                existingOverlay.remove();
            }

            fetch(`/services/${serviceId}/comment/`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.text();
                })
                .then(html => {
                    const overlay = document.createElement('div');
                    overlay.className = 'modal-overlay';
                    overlay.innerHTML = html;
                    document.body.appendChild(overlay);
                    setupCommentModal(serviceId);
                })
                .catch(error => {
                    console.error('Error:', error);
                    const errorContainer = document.createElement('div');
                    errorContainer.className = 'error-message';
                    errorContainer.textContent = `Error loading comment form: ${error.message}`;
                    document.body.appendChild(errorContainer);
                    setTimeout(() => errorContainer.remove(), 5000);
                });
        });
    });

    const hash = window.location.hash;
    if (hash?.startsWith('#comment-')) {
        const commentElement = document.querySelector(hash);
        if (commentElement) {
            commentElement.classList.add('highlight-comment');

            setTimeout(() => {
                commentElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });

                setTimeout(() => {
                    commentElement.classList.remove('highlight-comment');
                }, 2000);
            }, 300);
        }
    }

    const commentItems = document.querySelectorAll('.comment-item');
    commentItems.forEach(comment => {
        comment.addEventListener('mouseenter', () => {
            const actions = comment.querySelector('.comment-actions');
            if (actions) {
                actions.style.opacity = '1';
                actions.style.visibility = 'visible';
            }
        });

        comment.addEventListener('mouseleave', () => {
            const actions = comment.querySelector('.comment-actions');
            if (actions && !comment.querySelector('.reply-form-container:focus-within')) {
                actions.style.opacity = '0';
                actions.style.visibility = 'hidden';
            }
        });

        const replyBtn = comment.querySelector('.reply-btn');
        if (replyBtn) {
            replyBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const commentId = replyBtn.dataset.commentId;
                const replyForm = document.getElementById(`reply-form-${commentId}`);

                if (replyForm.style.display === 'none') {
                    replyForm.style.display = 'block';
                    replyForm.scrollIntoView({behavior: 'smooth', block: 'nearest'});
                } else {
                    replyForm.style.display = 'none';
                }
            });
        }
    });

    document.querySelectorAll('#comments-section form, #leave-comment-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitButton = form.querySelector('[type="submit"]');
            submitButton.disabled = true;

            // Use the form's action attribute properly
            const actionUrl = form.action;
            const formData = new FormData(form);

            // Handle parent comments for replies
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
                    // For modal form
                    if (form.id === 'leave-comment-form') {
                        const overlay = document.querySelector('.modal-overlay');
                        if (overlay) overlay.remove();
                    }

                    // For reply forms
                    if (commentId) {
                        document.getElementById(`reply-form-${commentId}`).style.display = 'none';
                    }

                    // Always redirect to the comment anchor
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    } else {
                        window.location.reload();
                    }
                } else {
                    // Error handling
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