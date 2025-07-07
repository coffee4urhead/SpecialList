document.addEventListener('DOMContentLoaded', function () {
    const options = document.querySelectorAll('#certificate-options .options > div');
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
    const uploadModal = document.querySelector('.upload-certificate-modal');
    const closeBtn = document.querySelector('.close-btn');

    if (uploadTrigger && uploadModal) {
        uploadTrigger.addEventListener('click', (e) => {
            e.preventDefault();
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

        if (!e.target.closest('#certificate-options')) {
            const optionsMenu = document.querySelector('#certificate-options .options');
            if (optionsMenu) {
                optionsMenu.style.display = 'none';
            }
        }
    });

    const gearIcon = document.querySelector('#certificate-options');
    if (gearIcon) {
        gearIcon.addEventListener('mouseenter', () => {
            document.querySelector('#certificate-options .options').style.display = 'block';
        });
    }
});

const editCertificateButton = document.querySelector('button.edit-btn');
let editModal = null;

if (editCertificateButton) {
    editCertificateButton.addEventListener('click', (e) => {
        const certificateId = e.currentTarget.dataset.certId;

        if (certificateId) {
            fetch(`/certificates/edit/${certificateId}/`)
                .then(res => res.json())
                .then(data => {
                    if (!editModal) {
                        editModal = document.createElement('div');
                        editModal.id = 'edit-certificate-modal-container';
                        document.body.appendChild(editModal);

                        editModal.addEventListener('click', (event) => {
                            if (event.target === editModal) {
                                editModal.querySelector('.edit-certificate-modal').classList.remove('active');
                            }
                        });
                    }

                    editModal.innerHTML = data.form_html;
                    const modalContent = editModal.querySelector('.edit-certificate-modal');
                    modalContent.classList.add('active');

                    const closeBtn = editModal.querySelector('.close-edit-btn');
                    if (closeBtn) {
                        closeBtn.addEventListener('click', () => {
                            modalContent.classList.remove('active');
                        });
                    }

                    const editForm = editModal.querySelector('#edit-certificate-form');
                    if (editForm) {
                        editForm.addEventListener('submit', (e) => {
                            e.preventDefault();
                            const formData = new FormData(editForm);

                            fetch(`/certificates/edit/${certificateId}/`, {
                                method: 'POST',
                                body: formData,
                                headers: {
                                    'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
                                },
                            })
                                .then(response => response.json())
                                .then(data => {
                                    if (data.success) {
                                        window.location.href = data.redirect_url;
                                    } else {
                                        console.error('Error updating certificate:', data.errors);
                                    }
                                })
                                .catch(error => {
                                    console.error('Error:', error);
                                });
                        });
                    }
                })
                .catch(error => {
                    console.error('Error loading edit form:', error);
                });
        }
    });
}