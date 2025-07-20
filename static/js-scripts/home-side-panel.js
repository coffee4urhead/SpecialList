document.addEventListener('DOMContentLoaded', function() {
    const hamburgerBtn = document.querySelector('.hamburger-btn');
    const sidePanel = document.querySelector('.side-panel');
    const header = document.querySelector('#head-sect');

    hamburgerBtn.addEventListener('click', function(e) {
        e.stopPropagation(); // Prevent event from bubbling up
        sidePanel.classList.toggle('active');
        this.classList.toggle('open');

        const isExpanded = this.getAttribute('aria-expanded') === 'true';
        this.setAttribute('aria-expanded', !isExpanded);
    });

    document.addEventListener('click', function(e) {
        if (!sidePanel.contains(e.target) && e.target !== hamburgerBtn) {
            sidePanel.classList.remove('active');
            hamburgerBtn.classList.remove('open');
            hamburgerBtn.setAttribute('aria-expanded', 'false');
        }
    });

    document.querySelectorAll('.side-panel a').forEach(link => {
        link.addEventListener('click', function() {
            sidePanel.classList.remove('active');
            hamburgerBtn.classList.remove('open');
            hamburgerBtn.setAttribute('aria-expanded', 'false');
        });
    });
});