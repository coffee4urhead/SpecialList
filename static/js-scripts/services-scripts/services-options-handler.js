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
});