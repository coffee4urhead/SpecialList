const uploaded_certificates = document.querySelectorAll('div.certificate-item');

uploaded_certificates.forEach((certificate) => {
    certificate.addEventListener('click', (e) => {
        certificate.style.backgroundColor = '#1d98a1';
        const previewUrl = certificate.dataset.previewUrl;
        const title = certificate.dataset.certificateTitle;
        const currentCertificatePreview = document.querySelector('img#certificate-file-preview');
        const previewContainer = document.querySelector('.pdf-preview-container');

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
    });
});