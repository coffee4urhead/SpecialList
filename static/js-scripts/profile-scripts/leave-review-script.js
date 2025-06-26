document.addEventListener('DOMContentLoaded', function() {
    // Handle Leave Review button click
    const leaveReviewBtn = document.getElementById('review-btn');
    if (leaveReviewBtn) {
        leaveReviewBtn.addEventListener('click', function() {
            const username = this.getAttribute('data-username');
            const reviewerId = this.getAttribute('data-reviewer-id');

            fetch(`/user/${username}/leaveReview/`)
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
                    setupReviewModal(username, reviewerId);
                })
                .catch(error => {
                    console.error('Error loading review form:', error);
                    alert('Error loading review form. Please try again.');
                });
        });
    }

    function setupReviewModal(username, reviewerId) {
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

        // Form submission
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();

                console.log(form)
                const formData = new FormData(form);
                   formData.append('reviewer_id', reviewerId);

                fetch(`/user/${username}/leaveReview/`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => {
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.json();
                })
                .then(data => {
                    if (data.status === 'success') {
                        overlay.remove();
                        alert('Review submitted successfully!');
                        window.location.reload();
                    } else {
                        console.error('Form errors:', data.errors);
                        // Display errors in the form
                        Object.entries(data.errors).forEach(([field, errors]) => {
                            const errorElement = document.createElement('div');
                            errorElement.className = 'error';
                            errorElement.textContent = errors.join(', ');

                            const fieldElement = form.querySelector(`[name="${field}"]`);
                            if (fieldElement) {
                                fieldElement.parentNode.appendChild(errorElement);
                            }
                        });
                    }
                })
                .catch(error => {
                    console.error('Error submitting review:', error);
                    alert('Error submitting review. Please try again.');
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
                    while(current) {
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