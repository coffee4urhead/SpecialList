import getCookie from "../utils.js";

document.addEventListener('DOMContentLoaded', () => {
    const toggleButton = document.createElement('div');
    toggleButton.className = 'panel-toggle';
    toggleButton.innerHTML = `
        <span class="toggle-icon">
            <svg viewBox="0 0 24 24">
                <path d="M8.59 16.58L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.42z"/>
            </svg>
        </span>
        <span class="toggle-text">Media Gallery</span>  
    `;

    const sidePanel = document.querySelector('.chat-side-panel-options');
    sidePanel.insertBefore(toggleButton, sidePanel.firstChild);

    const mediaGallery = document.querySelector('.media-gallery');

    toggleButton.addEventListener('click', () => {
        toggleButton.classList.toggle('active');
        mediaGallery.classList.toggle('active');
        if (mediaGallery.classList.contains('active')) {
            loadMediaGallery();
        }
    });

    const loadMediaGallery = async () => {
        const urlParams = new URLSearchParams(window.location.search);
        const conversationId = parseInt(urlParams.get('conversation_id') || CONVERSATION_ID);

        try {
            const response = await fetch(`/chats/api/images/?conversation_id=${conversationId}`, {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch media');
            }

            const data = await response.json();
            renderMediaGallery(data.media);
        } catch (error) {
            console.error('Error loading media gallery:', error);
            const galleryContainer = document.querySelector('.media-gallery .media-grid');
            if (galleryContainer) {
                galleryContainer.innerHTML = '<p>Error loading shared media. Please try again.</p>';
            }
        }
    };

    const renderMediaGallery = (mediaItems) => {
        const galleryContainer = document.querySelector('.media-gallery .media-grid');
        if (!galleryContainer) return;

        galleryContainer.innerHTML = '';

        if (!mediaItems || mediaItems.length === 0) {
            galleryContainer.innerHTML = '<p>No media shared yet</p>';
            return;
        }

        mediaItems.forEach(item => {
            const mediaElement = document.createElement('div');
            mediaElement.className = 'media-item';

            if (item.type === 'image') {
                mediaElement.innerHTML = `
                    <img src="${item.url}" alt="Shared image" loading="lazy">
                    <div class="media-meta">
                        <span>From: ${item.sender}</span>
                        <small>${new Date(item.timestamp).toLocaleString()}</small>
                    </div>
                `;
            } else if (item.type === 'video') {
                mediaElement.innerHTML = `
                    <video controls ${item.thumbnail ? `poster="${item.thumbnail}"` : ''}>
                        <source src="${item.url}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                    <div class="media-meta">
                        <span>From: ${item.sender}</span>
                        <small>${new Date(item.timestamp).toLocaleString()}</small>
                    </div>
                `;
            }

            galleryContainer.appendChild(mediaElement);
        });
    };

    const mediaTab = document.querySelector('[data-tab="media"]');
    if (mediaTab) {
        mediaTab.addEventListener('click', loadMediaGallery);
    } else {
        loadMediaGallery();
    }

    document.getElementById('style-btn').addEventListener('click', () => {
        document.getElementById('style-panel').classList.toggle('hidden');
    });

    document.getElementById('save-style').addEventListener('click', async () => {
        const color = document.getElementById('bubble-color-picker').value;
        const shape = document.getElementById('bubble-shape-picker').value;

        await fetch('/chats/api/chat-style/update/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({bubble_color: color, bubble_shape: shape}),
        });

        applyChatStyle(color, shape);
    });

    async function fetchChatStyle() {
        try {
            const res = await fetch('/chats/api/chat-style/');
            if (!res.ok) throw new Error('Failed to fetch style');
            const data = await res.json();
            applyChatStyle(data.bubble_color, data.bubble_shape);
        } catch (error) {
            console.error('Style fetch error:', error);
        }
    }

    function applyChatStyle(color, shape) {
        document.documentElement.style.setProperty('--bubble-color', color);
        document.body.classList.remove('shape-rounded', 'shape-sharp', 'shape-pill');
        document.body.classList.add(`shape-${shape}`);
    }

    fetchChatStyle();
});