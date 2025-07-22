import getCookie from "../utils.js";
import ChatClient from "../chats/chats.js";

document.addEventListener('DOMContentLoaded', function () {
    const messageButton = document.querySelector('.username-getter');

    messageButton.addEventListener('click', function () {
        const recipientUsername = this.dataset.username;
        const currentUserId = this.dataset.userId;
        startChatConnection(recipientUsername, currentUserId);
    });

    let chatClient = null;

    async function startChatConnection(recipientUsername, currentUserId) {
        const conversation = await getOrCreateConversation(recipientUsername);
        openChatWindow(conversation, currentUserId);
    }

    async function getOrCreateConversation(username) {
        const response = await fetch('/chats/api/conversations/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                participant: username
            })
        });
        return await response.json();
    }

    async function openChatWindow(conversation, currentUserId) {
        let chatWindow = document.getElementById('chat-window');

        if (chatWindow) {
            chatWindow.remove();
            if (chatClient) {
                chatClient.socket.close();
            }
        }

        chatClient = new ChatClient(conversation.id, currentUserId);

        if (!chatWindow) {
            chatWindow = document.createElement('div');
            chatWindow.id = 'chat-window';
            chatWindow.classList.add('active');
            chatWindow.innerHTML = `
                <div class="chat-header">
                    <h3>${conversation.other_user} <span class="user-status" style="font-size: 12px; margin-left: 10px; color: gray;">Offline</span></h3>
                    <button class="close-chat">×</button>
                    <button class="minimize-chat">−</button>
                </div>
                <div class="messages-container"></div>
                <div class="typing-indicator" style="display: none; font-style: italic; color: #888; margin: 5px 10px;"></div>
                <div class="chat-input">
                    <input name='message-typed' type="text" placeholder="Type a message...">
                    
                    <div class="media-upload-btn" title="Send Media">
                        <svg viewBox="0 0 12 13" width="20" height="20" fill="currentColor" aria-hidden="true" class="xfx01vb x1lliihq x1tzjh5l x1k90msu x2h7rmj x1qfuztq" style="--color: #32AE88;"><g fill-rule="evenodd" transform="translate(-450 -1073)"><g><path d="M99.825 918.322a2.55 2.55 0 0 1 .18-.712l-.489.043a1.601 1.601 0 0 0-.892.345 1.535 1.535 0 0 0-.557 1.321l.636 7.275c.01.12.186.123.199.003l.923-8.275zm4.67 1.591a1 1 0 1 1-1.991.175 1 1 0 0 1 1.991-.175m3.099 1.9a.422.422 0 0 0-.597-.05l-1.975 1.69a.288.288 0 0 0-.032.404l.442.526a.397.397 0 0 1-.606.51l-1.323-1.576a.421.421 0 0 0-.58-.063l-1.856 1.41-.265 2.246c-.031.357.173 1.16.53 1.19l6.345.397c.171.014.395-.02.529-.132.132-.111.38-.49.396-.661l.405-4.239-1.413-1.652z" transform="translate(352 156.5)"></path><path fill-rule="nonzero" d="m107.589 928.97-6.092-.532a1.56 1.56 0 0 1-1.415-1.687l.728-8.328a1.56 1.56 0 0 1 1.687-1.416l6.091.533a1.56 1.56 0 0 1 1.416 1.687l-.728 8.328a1.56 1.56 0 0 1-1.687 1.415zm.087-.996.06.002a.561.561 0 0 0 .544-.508l.728-8.328a.56.56 0 0 0-.507-.604l-6.09-.533a.56.56 0 0 0-.605.507l-.728 8.328a.56.56 0 0 0 .506.604l6.092.532z" transform="translate(352 156.5)"></path></g></g></svg>
                    </div>
                    <button class="send-btn"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg></button>
                        
                    <input type="file" id="chat-file-upload" accept="image/*,video/*" hidden>
                </div>
            `;

            document.body.appendChild(chatWindow);
            await loadPreviousMessages(conversation.id, currentUserId);

            const inputField = chatWindow.querySelector('input[name="message-typed"]');
            let typingTimeout;

            inputField.addEventListener('input', () => {
                chatClient.sendTypingIndicator(true);
                clearTimeout(typingTimeout);
                typingTimeout = setTimeout(() => {
                    chatClient.sendTypingIndicator(false);
                }, 1000);
            });

            chatWindow.querySelector('.media-upload-btn').addEventListener('click', () => {
                chatWindow.querySelector('#chat-file-upload').click();
            });

            chatWindow.querySelector('.minimize-chat').addEventListener('click', () => {
                chatWindow.classList.toggle('minimized');
            });
            chatWindow.querySelector('.send-btn').addEventListener('click', sendMessage);
            chatWindow.querySelector('input[type="text"]').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });
            chatWindow.querySelector('.close-chat').addEventListener('click', () => {
                chatWindow.remove();
                if (chatClient) {
                    chatClient.socket.close();
                    chatClient = null;
                }
            });
            chatWindow.querySelector('#chat-file-upload').addEventListener('change', handleFileUpload);
        }
    }

    function sendMessage() {
        const input = document.querySelector('#chat-window input[type="text"]');
        if (input.value.trim() && chatClient) {
            chatClient.sendTextMessage(input.value);
            input.value = '';
        }
    }

    function handleFileUpload(e) {
        if (e.target.files.length && chatClient) {
            chatClient.sendMediaMessage(e.target.files[0]);
            e.target.value = '';
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

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const messages = await response.json();

            const messagesContainer = document.querySelector('.messages-container');
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
                        <img src="${message.image}" style="max-width: 200px; max-height: 200px;">
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