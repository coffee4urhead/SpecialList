import getCookie from "../utils.js";

function showAlert(message, type = 'warning', timeout = 5000) {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = `
        ${message}
        <button onclick="this.parentElement.remove()" style="
            background: none;
            border: none;
            cursor: pointer;
            position: absolute;
            right: 10px;
            top: 10px;
        ">X</button>
    `;

    alertContainer.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, timeout);
}

document.addEventListener('DOMContentLoaded', function () {
    const options = document.querySelectorAll('#service-options .options > div');
    options.forEach(option => {
        const title = option.querySelector('h2');
        if (title) {
            title.addEventListener('click', (e) => {
                e.stopPropagation();
                option.classList.toggle('expanded');

                options.forEach(otherOption => {
                    if (otherOption !== option) {
                        otherOption.classList.remove('expanded');
                    }
                });
            });
        }
    });

    const uploadTrigger = document.querySelector('#show-upload-form');
    const uploadModal = document.querySelector('.upload-service-modal');
    const closeBtn = document.querySelector('.close-btn');

    if (uploadTrigger && uploadModal) {
        uploadTrigger.addEventListener('click', (e) => {
            e.preventDefault();

            const serviceOptions = document.getElementById('service-options');
            const canCreateMore = serviceOptions ?
                serviceOptions.dataset.canCreateMore === 'true' : false;

            if (!canCreateMore) {
                showAlert(
                    'You\'ve reached your service limit. ' +
                    '<a href="/subscriptions/offerSubscriptions/" style="color: #0056b3; text-decoration: underline;">Upgrade your plan</a> to create more services.',
                    'warning',
                    8000
                );
                return;
            }

            uploadModal.classList.add('active');
        });

        closeBtn.addEventListener('click', () => {
            uploadModal.classList.remove('active');
        });
    }

    window.addEventListener('click', (e) => {
        if (uploadModal && e.target === uploadModal) {
            uploadModal.classList.remove('active');
        }

        if (!e.target.closest('#service-options')) {
            const optionsMenu = document.querySelector('#service-options .options');
            if (optionsMenu) {
                optionsMenu.style.display = 'none';
            }
        }
    });

    const gearIcon = document.querySelector('#service-options');
    if (gearIcon) {
        gearIcon.addEventListener('mouseenter', () => {
            document.querySelector('#service-options .options').style.display = 'block';
        });
    }

    const likeButtons = document.querySelectorAll('button.like-button');
    const viewLikersButtons = document.querySelectorAll('.view-likers-button');
    const modal = document.getElementById('likers-modal');
    const modalContent = modal.querySelector('.modal-content');
    const likerList = document.getElementById('liker-list');
    const closeLikesModalBtn = document.querySelector('.close-likers-btn');

    viewLikersButtons.forEach(button => {
        button.addEventListener('click', function () {
            const serviceId = this.dataset.serviceId;

            fetch(`/services/${serviceId}/likers/`)
                .then(response => response.json())
                .then(data => {
                    likerList.innerHTML = '';

                    data.likers.forEach(user => {
                        const item = document.createElement('div');
                        item.className = 'liker-item';
                        item.innerHTML = `
                            <a href="/user/${user.username}">
                                <img src="${user.profile_pic || '/static/images/default-user.png'}" alt="${user.full_name}">
                            </a>
                            <div class="user-info">
                                <strong>${user.full_name}</strong>
                                <span>${user.username}</span>
                                <small>${user.joined_on}</small>  
                            </div>
                        `;
                        likerList.appendChild(item);
                    });

                    modal.classList.add('active');
                });
        });
    });

    closeLikesModalBtn.addEventListener('click', () => {
        modal.classList.remove('active');
    });

    window.addEventListener('click', function (event) {
        if (modal.classList.contains('active') && !modalContent.contains(event.target)) {
            modal.classList.remove('active');
        }
    });

    likeButtons.forEach(button => {
        button.addEventListener('click', function () {
            const serviceId = this.dataset.serviceId;
            const csrftoken = getCookie('csrftoken');

            fetch(`/services/${serviceId}/like/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json'
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.liked) {
                        this.querySelector('img').src = "/static/images/like-full.png";
                    } else {
                        this.querySelector('img').src = "/static/images/like-empty.png";
                    }
                    this.querySelector('.like-count-number').textContent = data.like_count;
                });
        });
    });

    const flagButtons = document.querySelectorAll('button.add-favorites');

    flagButtons.forEach(button => {
        button.addEventListener('click', function () {
            const serviceId = this.dataset.serviceId;
            const csrftoken = getCookie('csrftoken');

            fetch(`/services/${serviceId}/flagFavourite/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json'
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.flagged) {
                        this.querySelector('img').src = "/static/images/flag-full.png";
                    } else {
                        this.querySelector('img').src = "/static/images/flag-empty.png";
                    }
                    this.querySelector('.flag-count-number').textContent = data.flagged_count;
                });
        });
    });
});