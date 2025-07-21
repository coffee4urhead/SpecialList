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

    async function startChatConnection(recipientUsername, currentUserId) {  // Add parameter
        const conversation = await getOrCreateConversation(recipientUsername);
        chatClient = new ChatClient(conversation.id, currentUserId);
        openChatWindow(conversation);
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

    // Basic chat UI management (customize as needed)
    function openChatWindow(conversation) {
        let chatWindow = document.getElementById('chat-window');

        if (!chatWindow) {
            chatWindow = document.createElement('div');
            chatWindow.id = 'chat-window';
            chatWindow.innerHTML = `
                <div class="chat-header">
                    <h3>Chat with ${conversation.other_user}</h3>
                    <button class="close-chat">×</button>
                </div>
                <div class="messages-container"></div>
                <div class="chat-input">
                    <input type="text" placeholder="Type a message...">
                    <button class="send-btn">Send</button>
                    <input type="file" id="chat-file-upload" accept="image/*,video/*">
                </div>
            `;
            document.body.appendChild(chatWindow);

            // Add event listeners
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
            e.target.value = ''; // Reset input
        }
    }
});