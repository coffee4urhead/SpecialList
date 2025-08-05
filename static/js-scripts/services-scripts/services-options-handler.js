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
                                <img src="${user.profile_pic || '/static/images/avatar-default-photo.png'}" alt="${user.full_name}">
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

document.addEventListener('DOMContentLoaded', () => {
    const select = document.getElementById('service-to-delete');
    const form = document.getElementById('delete-service-form');

    if (select && form) {
        form.action = select.value;

        select.addEventListener('change', () => {
            form.action = select.value;
        });
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const serviceCreationForm = document.getElementById('service-creation-form');

    if (serviceCreationForm) {
        serviceCreationForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(this);
            const csrftoken = getCookie('csrftoken');

            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrftoken
                }
            })
                .then(response => {
                    if (response.redirected) {
                        window.location.href = response.url;
                    } else {
                        return response.json();
                    }
                })
                .then(data => {
                    if (data && data.success) {
                        window.location.reload();
                    } else if (data && data.errors) {
                        showAlert('Please fix the errors in the form', 'danger');
                        console.error(data.errors);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showAlert('Failed to create service', 'danger');
                });
        });
    }

    const form = document.getElementById('delete-service-form');
    if (!form) {
        console.warn('Delete service form not found');
        return;
    }

    form.addEventListener('submit', function (e) {
        console.log('Delete form submitted');
        e.preventDefault();

        const select = document.getElementById('service-to-delete');
        if (!select) {
            console.warn('Service select not found');
            return;
        }

        const deleteUrl = select.value;
        const csrftoken = getCookie('csrftoken');

        fetch(deleteUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            }
        })
            .then(response => {
                console.log("Raw response status:", response.status);
                return response.json();
            })
            .then(data => {
                console.log("Got response:", data);
                if (data.status === 'success') {
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    } else {
                        showAlert('Service deleted successfully!', 'success');
                    }
                } else {
                    showAlert('Failed to delete service', 'danger');
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
                showAlert('An error occurred.', 'danger');
            });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const editButton = document.querySelector(".edit-btn");
    const serviceSelect = document.querySelector("#service-to-edit");

    editButton.addEventListener("click", function () {
        const selectedServiceId = serviceSelect.value;

        if (!selectedServiceId) {
            alert("Please select a service to edit.");
            return;
        }

        fetch(`/services/${selectedServiceId}/edit/`)
            .then(response => response.json())
            .then(data => {
                if (data.form_html) {
                    showEditModal(data.form_html, selectedServiceId);
                }
            })
            .catch(error => {
                console.error("Error fetching edit form:", error);
            });
    });

    function showEditModal(html, serviceId) {
        const existingModal = document.querySelector(".edit-service-modal");
        if (existingModal) existingModal.remove();

        const wrapper = document.createElement("div");
        wrapper.innerHTML = html;
        document.body.appendChild(wrapper);

        wrapper.querySelector(".close-btn")?.addEventListener("click", () => wrapper.remove());
        wrapper.querySelector(".cancel-edit-btn")?.addEventListener("click", () => wrapper.remove());

        wrapper.addEventListener("click", function (e) {
            const modalContent = wrapper.querySelector(".edit-service-modal .modal-content");
            if (modalContent && !modalContent.contains(e.target)) {
                wrapper.remove();
            }
        });
        const form = wrapper.querySelector("#service-edit-form");
        if (form) {
            form.dataset.serviceId = serviceId;

            form.addEventListener("submit", function (e) {
                e.preventDefault();
                const formData = new FormData(form);
                const postUrl = `/services/${serviceId}/edit/`;

                fetch(postUrl, {
                    method: "POST",
                    body: formData
                })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            window.location.href = data.redirect_url;
                        } else {
                            showEditModal(data.form_html, serviceId);
                        }
                    })
                    .catch(err => console.error("Form submit error:", err));
            });
        }
    }
});