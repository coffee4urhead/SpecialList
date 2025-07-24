document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.filter-btn[data-filter]').forEach(button => {
        button.addEventListener('click', function () {
            const filterType = this.dataset.filter;
            const currentValue = this.dataset.value;
            const isActive = this.classList.contains('filled-web-btn');

            if (isActive) {
                this.classList.remove('filled-web-btn');
                this.classList.add('emp-web-btn');
            } else {
                this.classList.remove('emp-web-btn');
                this.classList.add('filled-web-btn');
            }

            const url = new URL(window.location);
            if (isActive) {
                url.searchParams.delete(filterType);
            } else {
                url.searchParams.set(filterType, currentValue);
            }
            window.location.href = url.toString();
        });
    });

    document.querySelectorAll('.price-range').forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            const priceRange = this.dataset.value;

            const url = new URL(window.location);
            url.searchParams.set('price_range', priceRange);
            window.location.href = url.toString();
        });
    });

    document.querySelectorAll('.location-filter').forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            const location = this.dataset.value;

            const url = new URL(window.location);
            url.searchParams.set('location', location);
            window.location.href = url.toString();
        });
    });

    const urlParams = new URLSearchParams(window.location.search);

    const activePriceRange = urlParams.get('price_range');
    if (activePriceRange) {
        const priceRangeBtn = document.querySelector('#priceRangeDropdown');
        priceRangeBtn.classList.remove('emp-web-btn');
        priceRangeBtn.classList.add('filled-web-btn');
    }

    const locationForm = document.querySelector('.location-popup form');
    if (locationForm) {
        locationForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const currentParams = new URLSearchParams(window.location.search);

            const locationInput = this.querySelector('input[name="location"]');
            if (locationInput.value) {
                currentParams.set('location', locationInput.value);
            } else {
                currentParams.delete('location');
            }

            window.location.search = currentParams.toString();
        });
    }

    document.querySelectorAll('.popup-toggle').forEach(button => {
        button.addEventListener('click', function () {
            const popup = this.nextElementSibling;
            popup.style.display = popup.style.display === 'block' ? 'none' : 'block';
        });
    });

    document.addEventListener('click', function (e) {
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.location-popup').forEach(popup => {
                popup.style.display = 'none';
            });
        }
    });
});