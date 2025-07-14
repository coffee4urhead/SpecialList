import getCookie from "../utils.js";

document.addEventListener('DOMContentLoaded', () => {
    const hash = window.location.hash;
    if (hash && hash.startsWith('#comment-')) {
        const commentElement = document.querySelector(hash);
        if (commentElement) {
            commentElement.scrollIntoView({behavior: 'smooth', block: 'start'});
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

    document.querySelectorAll('#comments-section form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(form);
            const commentId = form.closest('.reply-form-container')?.id.replace('reply-form-', '');

            if (commentId) {
                formData.append('parent_id', commentId);
            }

            const serviceId = window.location.pathname.split('/').filter(Boolean).pop();

            try {
                const response = await fetch(`/services/${serviceId}/comment/`, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: formData
                });

                const data = await response.json();

                if (data.status === 'success') {
                    window.location.href = data.redirect_url;
                } else {
                    alert('Error submitting comment: ' + (data.message || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error submitting comment');
            }
        });
    });
});