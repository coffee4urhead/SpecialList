document.addEventListener('DOMContentLoaded', function () {
    const imageObjectUrls = new WeakMap();

    function generateSectionPreview(form) {
        if (form.querySelector('[name$="-DELETE"]')?.checked) return '';
        const sectionType = form.dataset.sectionType || 'text_image';
        const title = form.querySelector('[name$="-title"]')?.value || '';
        const content = form.querySelector('[name$="-content"]')?.value || '';
        const listItems = form.querySelector('[name$="-list_items"]')?.value || '';
        const imageUrl = getImageUrl(form);

        return `<div class="service-section section-${sectionType}">
            ${title ? `<h2>${title}</h2>` : ''}
            ${generateSectionContent(sectionType, content, imageUrl, listItems, title)}
        </div>`;
    }

    function getImageUrl(form) {
        const fileInput = form.querySelector('[name$="-image"]');
        const existingImage = form.querySelector('.current-image')?.src;
        if (fileInput?.files.length > 0) {
            const url = URL.createObjectURL(fileInput.files[0]);
            imageObjectUrls.set(fileInput, url);
            return url;
        }
        return existingImage || '';
    }

    function generateSectionContent(type, content, imageUrl, listItems, title) {
        switch (type) {
            case'text_image':
                return `<div class="text-image-section">
                    <div class="text-content">${content.replace(/\n/g, '<br>')}</div>
                    ${imageUrl ? `<img src="${imageUrl}" width="300" alt="${title || 'Service image'}">` : ''}
                </div>`;
            case 'list':
                let items = [];
                try {
                    items = JSON.parse(listItems);
                    if (!Array.isArray(items)) items = [];
                } catch {
                    items = listItems.split('\n').filter(item => item.trim());
                }
                return `<ul class="list-section">
        ${items.length ? items.map(item => `<li>${item}</li>`).join('\n') : '<li class="empty">No items listed</li>'}
    </ul>`;
            case'text_only':
                return `<div class="text-content">${content.replace(/\n/g, '<br>')}</div>`;
            case'image_only':
                return imageUrl ? `<img src="${imageUrl}" style="max-width:100%" alt="${title || 'Service image'}">` : '';
            default:
                return '';
        }
    }

    function updateFullPreview() {
        const previewContainer = document.getElementById('live-preview');
        const forms = Array.from(document.querySelectorAll('.section-form'))
            .filter(form => !form.querySelector('[name$="-DELETE"]')?.checked);
        previewContainer.innerHTML = `<main id="extended-service-info-container">
            ${forms.map(generateSectionPreview).join('')}
        </main>`;
    }

    function handleImagePreview(input) {
        if (input.files.length) {
            if (imageObjectUrls.has(input)) URL.revokeObjectURL(imageObjectUrls.get(input));
            updateFullPreview();
        }
    }

    document.getElementById('sections-form').addEventListener('input', e => {
        if (e.target.matches('input, textarea, select')) updateFullPreview();
    });

    document.addEventListener('change', e => {
        if (e.target.matches('[name$="-image"]')) handleImagePreview(e.target);
    });

    window.addEventListener('beforeunload', () => {
        document.querySelectorAll('[name$="-image"]').forEach(input => {
            if (imageObjectUrls.has(input)) URL.revokeObjectURL(imageObjectUrls.get(input));
        });
    });

    updateFullPreview();
});