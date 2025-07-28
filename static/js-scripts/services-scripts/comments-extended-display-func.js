import getCookie from "../utils.js";

document.addEventListener('DOMContentLoaded', () => {
    scrollToHashComment();
    bindAllInitialCommentEvents();
    bindNewCommentForms();
});

function scrollToHashComment() {
    const hash = window.location.hash;
    if (hash?.startsWith('#comment-')) {
        const el = document.querySelector(hash);
        if (el) el.scrollIntoView({behavior: 'smooth', block: 'start'});
    }
}

function bindAllInitialCommentEvents() {
    document.querySelectorAll('.comment-item').forEach(bindCommentEvents);
}

function bindNewCommentForms() {
    document.querySelectorAll('#comments-section form:not([data-bound])').forEach(form => {
        form.dataset.bound = "true";
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(form);
            const replyFormContainer = form.closest('.reply-form-container');
            const parentId = replyFormContainer ? replyFormContainer.id.replace('reply-form-', '') : null;

            if (parentId) formData.append('parent_id', parentId);

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
                    const temp = document.createElement('div');
                    temp.innerHTML = (data.comment_html || '').trim();
                    const newComment = temp.firstElementChild;
                    if (!newComment) return;

                    bindCommentEvents(newComment);
                    bindNewCommentForms();

                    if (data.parent_id) {
                        const repliesContainer = document.getElementById(`replies-for-${data.parent_id}`);
                        if (repliesContainer) {
                            repliesContainer.appendChild(newComment);
                        }
                        const replyForm = document.getElementById(`reply-form-${data.parent_id}`);
                        if (replyForm) replyForm.style.display = 'none';
                    } else {
                        document.getElementById('comments-section').appendChild(newComment);
                    }

                    form.reset();
                } else {
                    alert('Error submitting comment: ' + (data.message || 'Unknown error'));
                }
            } catch {
                alert('An error occurred while submitting your comment.');
            }
        });
    });
}

function bindCommentEvents(commentEl) {
    const replyBtn = commentEl.querySelector('.reply-btn');
    if (replyBtn) {
        replyBtn.addEventListener('click', e => {
            e.stopPropagation();
            const commentId = replyBtn.dataset.commentId;
            const replyForm = document.getElementById(`reply-form-${commentId}`);
            if (replyForm) {
                const isHidden = replyForm.style.display === 'none';
                replyForm.style.display = isHidden ? 'block' : 'none';
                if (isHidden) replyForm.scrollIntoView({behavior: 'smooth', block: 'nearest'});
            }
        });
    }

    commentEl.addEventListener('mouseenter', () => {
        const actions = commentEl.querySelector('.comment-actions');
        if (actions) {
            actions.style.opacity = '1';
            actions.style.visibility = 'visible';
        }
    });

    commentEl.addEventListener('mouseleave', () => {
        const actions = commentEl.querySelector('.comment-actions');
        const formFocused = commentEl.querySelector('.reply-form-container:focus-within');
        if (actions && !formFocused) {
            actions.style.opacity = '0';
            actions.style.visibility = 'hidden';
        }
    });
}
