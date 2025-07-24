document.addEventListener('DOMContentLoaded', function() {
    const availabilityForm = document.getElementById('working-time-form');

    availabilityForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const formData = new FormData(this);
        const submitButton = this.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.textContent = 'Saving...';

        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => Promise.reject(err));
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const weeklyTimestamps = document.querySelector('.weekly-timestamps');

                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = data.table_html;
                console.log(tempDiv);
                const newTable = tempDiv.querySelector('table.availability-table');
                console.log(newTable);
                if (newTable && weeklyTimestamps) {
                    const oldTable = weeklyTimestamps.querySelector('table.availability-table');

                    if (oldTable) {
                        oldTable.replaceWith(newTable);
                    } else {
                        weeklyTimestamps.appendChild(newTable);
                    }

                    showToast('Availability updated successfully!');
                } else {
                    console.error('Could not find table container or new table');
                }
            } else {
                displayFormErrors(data.errors);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('An error occurred. Please try again.');
        })
        .finally(() => {
            submitButton.disabled = false;
            submitButton.textContent = 'Submit';
        });
    });

    function displayFormErrors(errors) {
        document.querySelectorAll('.form-error').forEach(el => {
            el.textContent = '';
        });

        for (const field in errors) {
            const fieldElement = document.querySelector(`[name="${field}"]`);
            if (fieldElement) {
                const errorContainer = fieldElement.closest('.form-group').querySelector('.form-error');
                if (errorContainer) {
                    errorContainer.textContent = errors[field][0];
                }
            }
        }
    }

    function showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
});