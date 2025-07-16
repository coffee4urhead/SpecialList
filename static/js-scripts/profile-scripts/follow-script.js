import {getCookie} from './get_location.js'

const followBtn = document.querySelector('button.filled-web-btn');
if (followBtn) {
    followBtn.addEventListener('click', function () {
        const action = this.dataset.action;
        const username = this.dataset.username;
        const followerId = this.dataset.followerId;

        fetch(`/user/${username}/connections/updateConnection/${followerId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                action: action,
                username: username
            })
        })
            .then(res => {
                if (!res.ok) {
                    throw new Error(`Network response was not ok, status: ${res.status}`);
                }
                return res.json();
            })
            .then(data => {
                console.log('Response JSON:', data);
                if (data.status === 'success') {
                    if (this.classList.contains('follow')) {
                    this.innerText = 'Unfollow Account';
                    this.dataset.action = 'unfollow';
                    this.classList.remove('follow');
                    this.classList.add('unfollow');
                } else {
                    this.innerText = 'Follow Account';
                    this.dataset.action = 'follow';
                    this.classList.remove('unfollow');
                    this.classList.add('follow');
                }
                    window.location.reload();
                } else {
                    console.warn('Action not successful:', data.message);
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
            });
    });
}