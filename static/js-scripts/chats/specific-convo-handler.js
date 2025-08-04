import getCookie from "../utils.js";
import ChatClient from "../chats/chats.js";

function generateThumbnail(videoFile) {
    return new Promise((resolve) => {
        const video = document.createElement('video');
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');

        video.src = URL.createObjectURL(videoFile);
        video.addEventListener('loadedmetadata', () => {
            const ratio = video.videoWidth / video.videoHeight;
            canvas.width = 200;
            canvas.height = 200 / ratio;

            video.currentTime = video.duration * 0.25;
        });

        video.addEventListener('seeked', () => {
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            const thumbnail = canvas.toDataURL('image/jpeg');
            URL.revokeObjectURL(video.src);
            resolve(thumbnail);
        });
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const chatClient = new ChatClient(CONVERSATION_ID, CURRENT_USER_ID);

    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const messagesContainer = document.getElementById('messages-container');
    const typingIndicator = document.getElementById('typing-indicator');
    const mediaUploadBtn = document.getElementById('media-upload-btn');
    const fileInput = document.getElementById('chat-file-upload');

    loadPreviousMessages(CONVERSATION_ID, CURRENT_USER_ID);

    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendMessage();
    });

    let typingTimeout;
    messageInput.addEventListener('input', function () {
        chatClient.sendTypingIndicator(true);
        clearTimeout(typingTimeout);
        typingTimeout = setTimeout(() => {
            chatClient.sendTypingIndicator(false);
        }, 1000);
    });

    mediaUploadBtn.addEventListener('click', function () {
        fileInput.click();
    });

    fileInput.addEventListener('change', function (e) {
        if (e.target.files.length) {
            const file = e.target.files[0];

            if (file.type.startsWith('video/')) {
                generateThumbnail(file).then(thumbnail => {
                    chatClient.sendVideoMessage(file, thumbnail);
                });
            } else if (file.type.startsWith('image/')) {
                chatClient.sendMediaMessage(file);
            } else {
                alert('Unsupported file type. Please upload an image or video.');
            }

            e.target.value = '';
        }
    });

    function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            chatClient.sendTextMessage(message);
            messageInput.value = '';
        }
    }

    async function loadSharedMedia() {
        try {
            const response = await fetch(`/chats/api/conversation/media/?conversation_id=${CONVERSATION_ID}`, {
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const mediaGrid = document.querySelector('.media-grid');

            if (!mediaGrid) {
                console.error('Media grid element not found');
                return;
            }

            mediaGrid.innerHTML = '';

            if (!data.media || data.media.length === 0) {
                mediaGrid.innerHTML = '<p>No shared media yet</p>';
                return;
            }

            data.media.forEach(item => {
                const mediaElement = document.createElement('div');
                mediaElement.className = 'media-item';

                if (item.type === 'image') {
                    mediaElement.innerHTML = `
                    <img src="${item.url}" loading="lazy">
                    <div class="media-info">
                        <span>From ${item.sender}</span>
                        <small>${new Date(item.timestamp).toLocaleDateString()}</small>
                    </div>
                `;
                } else if (item.type === 'video') {
                    mediaElement.innerHTML = `
                    <div class="video-container">
                        <video controls ${item.thumbnail ? `poster="${item.thumbnail}"` : ''}>
                            <source src="${item.url}" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                        <div class="media-info">
                            <span>From ${item.sender}</span>
                            <small>${new Date(item.timestamp).toLocaleDateString()}</small>
                        </div>
                    </div>
                `;
                }

                mediaElement.addEventListener('click', () => {
                    showMediaPopup(item);
                });

                mediaGrid.appendChild(mediaElement);
            });
        } catch (error) {
            console.error('Error loading shared media:', error);
            const mediaGrid = document.querySelector('.media-grid');
            if (mediaGrid) {
                mediaGrid.innerHTML = `<p>Error loading shared media: ${error.message}</p>`;
            }
        }
    }

    function showMediaPopup(mediaItem) {
        const popup = document.createElement('div');
        popup.className = 'media-popup';

        if (mediaItem.type === 'image') {
            popup.innerHTML = `
                <div class="popup-content">
                    <img src="${mediaItem.url}">
                    <button class="close-popup">&times;</button>
                </div>
            `;
        } else if (mediaItem.type === 'video') {
            popup.innerHTML = `
                <div class="popup-content">
                    <video controls autoplay ${mediaItem.thumbnail ? `poster="${mediaItem.thumbnail}"` : ''}>
                        <source src="${mediaItem.url}" type="video/mp4">
                    </video>
                    <button class="close-popup">&times;</button>
                </div>
            `;
        }

        popup.querySelector('.close-popup').addEventListener('click', () => {
            document.body.removeChild(popup);
        });

        document.body.appendChild(popup);
    }

    async function loadPreviousMessages(conversationId, currentUserId) {
        try {
            const response = await fetch(`/chats/api/messages/?conversation_id=${conversationId}`, {
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                }, credentials: 'include'
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const messages = await response.json();
            messagesContainer.innerHTML = '';

            messages.forEach(message => {
                const messageElement = document.createElement('div');
                messageElement.className = `message ${message.sender_id == currentUserId ? 'sent' : 'received'}`;

                if (message.content) {
                    messageElement.innerHTML = `
                        <div class="message-content">${message.content}</div>
                        <div class="message-time">${formatTimestamp(message.timestamp)}</div>
                    `;
                } else if (message.image) {
                    messageElement.innerHTML = `
                        <div class="message-media">
                            <img src="${message.image}" loading="lazy">
                        </div>
                        <div class="message-time">${formatTimestamp(message.timestamp)}</div>
                    `;
                } else if (message.video) {
                    messageElement.innerHTML = `
                        <div class="message-media">
                            <video controls ${message.thumbnail ? `poster="${message.thumbnail}"` : ''}>
                                <source src="${message.video}" type="video/mp4">
                                Your browser does not support the video tag.
                            </video>
                        </div>
                        <div class="message-time">${formatTimestamp(message.timestamp)}</div>
                    `;
                }

                messagesContainer.appendChild(messageElement);
            });

            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        } catch (error) {
            console.error('Error loading previous messages:', error);
        }
    }

    function formatTimestamp(timestamp) {
        if (!timestamp) return '';
        try {
            const date = new Date(timestamp);
            return date.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
        } catch (e) {
            return timestamp;
        }
    }

    loadSharedMedia();

    const emojiBtn = document.getElementById('emoji-btn');
    const emojiPicker = document.getElementById('emoji-picker');

    emojiBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        emojiPicker.classList.toggle('hidden');
    });

    emojiPicker.addEventListener('emoji-click', (event) => {
        messageInput.value += event.detail.unicode;
        messageInput.focus();
    });

    document.addEventListener('click', (event) => {
        if (!emojiBtn.contains(event.target) && !emojiPicker.contains(event.target)) {
            emojiPicker.classList.add('hidden');
        }
    });
});