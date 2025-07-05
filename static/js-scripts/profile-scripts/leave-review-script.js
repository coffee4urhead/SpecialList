document.addEventListener('DOMContentLoaded', function() {
    // Handle Leave Review button click
    const leaveReviewBtn = document.getElementById('review-btn');
    if (leaveReviewBtn) {
        leaveReviewBtn.addEventListener('click', function() {
            const username = this.getAttribute('data-username');
            const reviewerId = this.getAttribute('data-reviewer-id');

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

    function setupReviewModal(username) {
        const overlay = document.querySelector('.modal-overlay');
        const form = document.getElementById('review-form');

        if (!overlay) return;

        // Close modal
        overlay.addEventListener('click', function(e) {
            if (e.target.classList.contains('modal-overlay') ||
                e.target.classList.contains('close-modal')) {
                overlay.remove();
            }
        });

        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();

                // Clear previous errors
                document.querySelectorAll('.error').forEach(el => el.remove());

                const formData = new FormData(form);

                fetch(`/reviews/user/${username}/leaveReview/`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => {
                    const contentType = response.headers.get('content-type');
                    if (!contentType || !contentType.includes('application/json')) {
                        return response.text().then(text => {
                            throw new Error('Server returned non-JSON response');
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.status === 'success') {
                        overlay.remove();
                        window.location.reload();
                    } else if (data.errors) {
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
                    console.error('Error submitting review:', error);
                    alert('Error submitting review. Please check the form and try again.');
                });
            });
        }

        // Star rating functionality
        const starContainer = overlay.querySelector('.star-rating');
        if (starContainer) {
            starContainer.addEventListener('click', function(e) {
                if (e.target.tagName === 'LABEL') {
                    const radio = e.target.previousElementSibling;
                    radio.checked = true;

                    // Update star colors
                    const stars = starContainer.querySelectorAll('label');
                    stars.forEach(star => star.style.color = '#ddd');

                    let current = e.target;
                    while (current) {
                        if (current.tagName === 'LABEL') {
                            current.style.color = 'gold';
                        }
                        current = current.previousElementSibling;
                    }
                }
            });
        }
    }
});