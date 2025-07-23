import getCookie from "../utils.js";
import ChatClient from "../chats/chats.js";

document.addEventListener('DOMContentLoaded', function () {
    const chatClient = new ChatClient(
        CONVERSATION_ID,
        CURRENT_USER_ID
    );

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
            chatClient.sendMediaMessage(e.target.files[0]);
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

    async function loadPreviousMessages(conversationId, currentUserId) {
        try {
            const response = await fetch(`/chats/api/messages/?conversation_id=${conversationId}`, {
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                credentials: 'include'
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
                                    <img src="${message.image}">
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
});