function setupReviewModal(username, reviewId = null) {
    const overlay = document.querySelector('.modal-overlay');
    const form = document.getElementById('review-form');

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
        const endpoint = reviewId
            ? `/reviews/user/${username}/editReview/${reviewId}/`
            : `/reviews/user/${username}/leaveReview/`;

        fetch(endpoint, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    overlay.remove();
                    window.location.reload(); // Refresh to show updated review
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
        // Star rating functionality
        const starContainer = overlay.querySelector('.star-rating');
        if (starContainer) {
            starContainer.addEventListener('click', function (e) {
                if (e.target.tagName === 'LABEL') {
                    const radio = e.target.previousElementSibling;
                    if (radio) radio.checked = true;

                    const allLabels = Array.from(starContainer.querySelectorAll('label'));
                    allLabels.forEach(label => {
                        label.style.color = '#ddd';
                    });

                    let fill = false;
                    for (let i = allLabels.length - 1; i >= 0; i--) {
                        const label = allLabels[i];
                        if (label === e.target) {
                            fill = true;
                        }
                        if (fill) {
                            label.style.color = 'gold';
                        }
                    }
                }
            });
        }
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const leaveReviewBtn = document.getElementById('review-btn');
    if (leaveReviewBtn) {
        leaveReviewBtn.addEventListener('click', function () {
            const username = this.getAttribute('data-username');

            fetch(`/reviews/user/${username}/leaveReview/`)
                .then(response => {
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.text();
                })
                .then(html => {
                    document.body.insertAdjacentHTML('beforeend', `
                        <div class="modal-overlay">
                            ${html}
                        </div>
                    `);
                    setupReviewModal(username);
                })
                .catch(error => {
                    console.error('Error loading review form:', error);
                    alert('Error loading review form. Please try again.');
                });
        });
    }

    // Handle Edit Review button clicks
    document.querySelectorAll('.edit-rev').forEach(editBtn => {
        editBtn.addEventListener('click', function () {
            const username = this.getAttribute('data-username');
            const reviewId = this.getAttribute('data-review-id');

            fetch(`/reviews/user/${username}/editReview/${reviewId}/`)
                .then(response => {
                    if (!response.ok) throw new Error('Failed to load edit form');
                    return response.text();  // Get the form HTML
                })
                .then(html => {
                    document.body.insertAdjacentHTML('beforeend', `<div class="modal-overlay">${html}</div>`);
                    setupReviewModal(username, reviewId);
                })
                .catch(error => {
                    console.error('Error loading edit form:', error);
                    alert('Could not load edit form. Please try again.');
                });
        });
    });
});
