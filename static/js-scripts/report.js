import getCookie from "./utils.js";

document.addEventListener('DOMContentLoaded', function () {
    const reportModal = document.createElement('div');
    reportModal.className = 'report-modal';
    reportModal.innerHTML = `
        <div class="report-form-container">
            <button class="close-report-btn">&times;</button>
            <h2>Report Content</h2>
            <div id="report-form-placeholder"></div>
        </div>
    `;
    document.body.appendChild(reportModal);

    const modal = document.querySelector('.report-modal');
    const formPlaceholder = document.getElementById('report-form-placeholder');
    const closeBtn = document.querySelector('.close-report-btn');

    document.addEventListener('click', function (e) {
        const reportBtn = e.target.closest('.report-service, .report-comment, .report-user, .report-review');
        if (reportBtn) {
            e.preventDefault();
            const contentId = reportBtn.dataset.serviceId ||
                reportBtn.dataset.commentId ||
                reportBtn.dataset.userId ||
                reportBtn.dataset.reviewId;

            const contentType = reportBtn.classList.contains('report-service') ? 'service' :
                reportBtn.classList.contains('report-comment') ? 'comment' :
                    reportBtn.classList.contains('report-review') ? 'review' : 'user';

            fetchReportForm(contentType, contentId);
        }
    });

    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', function (e) {
        if (e.target === modal) {
            closeModal();
        }
    });

    formPlaceholder.addEventListener('submit', function (e) {
        if (e.target.id === 'report-form') {
            e.preventDefault();
            submitReportForm(e.target);
        }
    });

    function fetchReportForm(contentType, objectId) {
        fetch('/services/report/', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    formPlaceholder.innerHTML = data.form_html;
                    const form = document.getElementById('report-form');
                    form.dataset.contentType = contentType;
                    form.dataset.objectId = objectId;
                    modal.classList.add('active');

                    const cancelBtn = form.querySelector('.cancel-btn');
                    if (cancelBtn) {
                        cancelBtn.addEventListener('click', () => {
                            closeModal();
                            showAlert('warning', 'Frequently reporting may result in bans so be careful and mindful!');
                        });
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching report form:', error);
            });
    }

    function submitReportForm(form) {
        const formData = new FormData(form);
        formData.append('content_type', form.dataset.contentType);
        formData.append('object_id', form.dataset.objectId);

        const submitBtn = form.querySelector('.submit-btn');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';

        fetch('/services/report/', {
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
                    showAlert('success', data.message);
                    closeModal();
                } else {
                    formPlaceholder.innerHTML = data.form_html;
                }
            })
            .catch(error => {
                console.error('Error submitting report:', error);
            });
    }

    function closeModal() {
        modal.classList.remove('active');
    }
});

function showAlert(type, message) {
    let container = document.getElementById('alert-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'alert-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        document.body.appendChild(container);
    }

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <span>${message}</span>
        <button>&times;</button>
    `;

    alert.querySelector('button').addEventListener('click', () => alert.remove());

    container.appendChild(alert);

    setTimeout(() => {
        alert.remove();
        if (container.children.length === 0) {
            container.remove();
        }
    }, 5000);
}

document.addEventListener('DOMContentLoaded', function () {
    if (window.location.hash) {
        const elementId = window.location.hash.substring(1);
        scrollToContent(elementId);
    }
});

function scrollToContent(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('reported-content-highlight');

        element.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });

        setTimeout(() => {
            element.classList.remove('reported-content-highlight');
        }, 3000);
    }
}