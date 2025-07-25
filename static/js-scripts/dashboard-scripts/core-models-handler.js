document.addEventListener("DOMContentLoaded", function () {
    const popup = document.getElementById("user-popup-overlay");
    const popupList = document.getElementById("popup-list");
    const popupTitle = document.getElementById("popup-title");
    const closeBtn = document.getElementById("close-popup");

    const templates = {
        "user-template": document.getElementById("user-template"),
        "org-template": document.getElementById("org-template"),
        "cert-template": document.getElementById("cert-template"),
        "services-template": document.getElementById("services-template"),
        "availabilities-template": document.getElementById("availabilities-template"),
        "comments-template": document.getElementById("comments-template"),
    };

    document.querySelectorAll(".stat-card").forEach(card => {
        card.addEventListener("click", () => {
            const target = card.dataset.popupTarget;

            popupList.innerHTML = "";

            const template = templates[target];
            if (template) {
                const readable = target.replace('-template', '').replace(/^\w/, c => c.toUpperCase());
                popupTitle.textContent = `Viewing ${readable}`;
                popupList.append(...Array.from(template.children).map(el => el.cloneNode(true)));
                popup.classList.remove("hidden");
                popup.classList.add("visible");
            }
        });
    });

    closeBtn.addEventListener("click", () => {
        popup.classList.remove("visible");
        popup.classList.add("hidden");
    });

    popupList.addEventListener('click', (event) => {
        const card = event.target.closest('.user-card');
        if (!card) return;

        const type = card.dataset.type;
        const id = card.dataset.id;

        if (!type || !id) return;

        let adminUrl;
        switch (type) {
            case 'user':
                adminUrl = `/admin/core/customuser/${id}/change/`;
                break;
            case 'organization':
                adminUrl = `/admin/core/organization/${id}/change/`;
                break;
            case 'certificate':
                adminUrl = `/admin/core/certificate/${id}/change/`;
                break;
            case 'service':
                adminUrl = `/admin/services/servicelisting/${id}/change/`;
                break;
            case 'availability':
                adminUrl = `/admin/eservices/availability/${id}/change/`;
                break;
            case 'comment':
                adminUrl = `/admin/services/comment/${id}/change/`;
                break;
            default:
                return;
        }

        window.open(adminUrl, '_blank');
    });

});
