const uploaded_certificates = document.querySelectorAll('div.certificate-item');

uploaded_certificates.forEach((certificate) => {
    certificate.addEventListener('click', (e) => {

        uploaded_certificates.forEach(cert => {
            cert.style.backgroundColor = '';
        });

        certificate.style.backgroundColor = '#1d98a1';
        const previewUrl = certificate.dataset.previewUrl;
        const title = certificate.dataset.certificateTitle;
        const currentCertificatePreview = document.querySelector('img#certificate-file-preview');
        const previewContainer = document.querySelector('.pdf-preview-container');
        const deleteForm = document.querySelector('form[method="post"]');

        if (previewUrl) {
            if (currentCertificatePreview) {
                currentCertificatePreview.src = previewUrl;
                currentCertificatePreview.alt = title;

                const titleElement = currentCertificatePreview.nextElementSibling;
                if (titleElement && titleElement.tagName === 'H2') {
                    titleElement.querySelector('a').textContent = title;
                }
            } else {
                const img = document.createElement('img');
                img.src = previewUrl;
                img.alt = title;
                img.id = 'certificate-file-preview';

                const titleElement = document.createElement('h2');
                titleElement.innerHTML = `<a>${title}</a>`;

                previewContainer.innerHTML = '';
                previewContainer.appendChild(img);
                previewContainer.appendChild(titleElement);
            }
        } else {
            previewContainer.innerHTML = '<p>Preview not available</p>';
        }

        if (deleteForm) {
            const certificateId = certificate.dataset.certificateId;
            if (!certificateId) {
                console.error('Certificate ID is missing!');
                return;
            }
            deleteForm.action = `/certificates/delete/${certificateId}/`;

            const editButton = document.querySelector('.edit-btn');
            if (editButton) {
                editButton.dataset.certId = certificateId;
            }

            const formTitleElement = deleteForm.querySelector('#bottom-cont-holder h2 a');
            if (formTitleElement) {
                formTitleElement.textContent = title;
            }
        }
    });
});