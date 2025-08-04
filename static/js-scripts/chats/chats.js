import {v4 as uuidv4} from 'https://cdn.skypack.dev/uuid';

export default class ChatClient {
    constructor(conversationId, userId) {
        this.conversationId = conversationId;
        this.userId = userId;
        this.socket = new WebSocket(
            `ws://${window.location.host}/ws/chat/${conversationId}/`
        );

        this.socket.onopen = () => {
            console.log(`[WebSocket] Connected to conversation ${this.conversationId}`);
        };

        this.socket.onerror = (e) => {
            console.log('[WebSocket] Error:', e);
            setTimeout(() => this.reconnect(), 5000);
        };

        this.socket.onclose = (e) => {
            console.log('[WebSocket] Closed:', e);
            setTimeout(() => this.reconnect(), 5000);
        };

        this.setupEventHandlers();
        this.setupPing();
        this.setupEventHandlers();
        this.setupPing();
    }

    setupEventHandlers() {
        this.socket.onmessage = (e) => {
            const data = JSON.parse(e.data);

            switch (data.type) {
                case 'text_message':
                    this.handleTextMessage(data);
                    break;
                case 'media_message':
                    this.handleMediaMessage(data);
                    break;
                case 'video_message':
                    this.handleMediaMessage(data);
                    break;
                case 'typing':
                    this.handleTypingIndicator(data);
                    break;
                case 'read_receipt':
                    this.handleReadReceipt(data);
                    break;
                case 'user_status':
                    this.handleUserStatus(data);
                    break;
            }
        };

        this.socket.onclose = (e) => {
            console.log('Chat socket closed unexpectedly');
            setTimeout(() => this.reconnect(), 5000);
        };
    }

    setupPing() {
        setInterval(() => {
            if (this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify({type: 'ping'}));
            }
        }, 30000);
    }

    reconnect() {
        this.socket = new WebSocket(
            `ws://${window.location.host}/ws/chat/${this.conversationId}/`
        );
        this.setupEventHandlers();
    }

    sendTextMessage(content) {
        if (this.socket.readyState !== WebSocket.OPEN) {
            console.warn('WebSocket not open');
            return;
        }

        const tempId = uuidv4();
        const timestamp = new Date();

        const messagesContainer = document.querySelector('.messages-container');
        if (messagesContainer) {
            const messageElement = document.createElement('div');
            messageElement.className = `message sent`;
            messageElement.setAttribute('data-id', tempId);
            messageElement.innerHTML = `
            <div class="message-content">${content}</div>
            <div class="message-time">${timestamp.toLocaleTimeString()}</div>
        `;
            messagesContainer.appendChild(messageElement);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        this.socket.send(JSON.stringify({
            type: 'text_message',
            message: content,
            temp_id: tempId
        }));
    }

    sendMediaMessage(file) {
        if (this.socket.readyState !== WebSocket.OPEN) {
            console.warn('WebSocket not open');
            return;
        }

        const tempId = uuidv4();
        const timestamp = new Date();

        const reader = new FileReader();
        reader.onload = (e) => {
            const base64Image = e.target.result;

            const messagesContainer = document.querySelector('.messages-container');
            if (messagesContainer) {
                const messageElement = document.createElement('div');
                messageElement.className = `message sent`;
                messageElement.setAttribute('data-id', tempId);
                messageElement.innerHTML = `
                <div class="message-media">
                    <img src="${base64Image}" style="max-width: 200px; max-height: 200px;">
                </div>
                <div class="message-time">${timestamp.toLocaleTimeString()}</div>
            `;
                messagesContainer.appendChild(messageElement);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }

            this.socket.send(JSON.stringify({
                type: 'media_message',
                image: base64Image,
                temp_id: tempId
            }));
        };

        reader.readAsDataURL(file);
    }

    sendTypingIndicator(typing) {
        this.socket.send(JSON.stringify({
            type: 'typing',
            typing: typing
        }));
    }

    sendReadReceipt(data) {
        let message_ids = [];

        if (Array.isArray(data)) {
            message_ids = data;
        } else if (data && Array.isArray(data.message_ids)) {
            message_ids = data.message_ids;
            if (data.reader_id === this.userId) {
                return;
            }
        } else {
            console.warn('sendReadReceipt: invalid data', data);
            return;
        }

        message_ids.forEach(id => {
            const msgEl = document.querySelector(`.message[data-id="${id}"]`);
            if (msgEl) {
                msgEl.classList.add('read');
                const readTick = msgEl.querySelector('.read-indicator');
                if (readTick) readTick.style.visibility = 'visible';
            }
        });
    }


    handleTextMessage(data) {
        if (parseInt(data.sender_id) === parseInt(this.userId)) return;

        const messagesContainer = document.querySelector('.messages-container');
        if (messagesContainer) {
            const messageElement = document.createElement('div');
            messageElement.className = `message received`;
            messageElement.setAttribute('data-id', data.message_id);
            messageElement.innerHTML = `
            <div class="message-content">${data.message}</div>
            <div class="message-time">${new Date(data.timestamp).toLocaleTimeString()}</div>
        `;
            messagesContainer.appendChild(messageElement);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

            this.sendReadReceipt([data.message_id]);
        }
    }

    sendVideoMessage(file, thumbnail = null) {
        if (this.socket.readyState !== WebSocket.OPEN) {
            console.warn('WebSocket not open');
            return;
        }

        const tempId = uuidv4();
        const timestamp = new Date();

        const reader = new FileReader();
        reader.onload = (e) => {
            const base64Video = e.target.result;

            const messagesContainer = document.querySelector('.messages-container');
            if (messagesContainer) {
                const messageElement = document.createElement('div');
                messageElement.className = `message sent`;
                messageElement.setAttribute('data-id', tempId);
                messageElement.innerHTML = `
                <div class="message-media">
                    <video controls style="max-width: 200px; max-height: 200px;" ${
                    thumbnail ? `poster="${thumbnail}"` : ''
                }>
                        <source src="${base64Video}" type="${file.type}">
                        Your browser does not support the video tag.
                    </video>
                </div>
                <div class="message-time">${timestamp.toLocaleTimeString()}</div>
            `;
                messagesContainer.appendChild(messageElement);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }

            this.socket.send(JSON.stringify({
                type: 'media_message',
                video: base64Video,
                temp_id: tempId,
                thumbnail_url: thumbnail
            }));
        };

        reader.readAsDataURL(file);
    }

    handleMediaMessage(data) {
        if (parseInt(data.sender_id) === parseInt(this.userId)) return;

        const messagesContainer = document.querySelector('.messages-container');
        if (!messagesContainer) return;

        const messageElement = document.createElement('div');
        messageElement.className = `message ${data.sender_id === this.userId ? 'sent' : 'received'}`;

        let mediaHtml = '';
        if (data.image_url) {
            mediaHtml = `
            <img src="${data.image_url}" 
                 style="max-width: 200px; max-height: 200px;"
                 loading="lazy">`;
        } else if (data.video_url) {
            mediaHtml = `
            <video controls 
                   style="max-width: 200px; max-height: 200px;"
                   ${data.thumbnail_url ? `poster="${data.thumbnail_url}"` : ''}>
                <source src="${data.video_url}" type="video/mp4">
                Your browser does not support the video tag.
            </video>`;
        }

        messageElement.innerHTML = `
        <div class="message-media">
            ${mediaHtml}
        </div>
        <div class="message-time">${new Date(data.timestamp).toLocaleTimeString()}</div>
    `;

        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        if (data.message_id && data.sender_id !== this.userId) {
            this.sendReadReceipt([data.message_id]);
        }
    }

    handleTypingIndicator(data) {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (!typingIndicator) return;

        if (data.typing && data.user_id !== this.userId) {
            typingIndicator.style.display = 'block';
            typingIndicator.textContent = `${data.username} is typing...`;

            clearTimeout(this._typingTimeout);
            this._typingTimeout = setTimeout(() => {
                typingIndicator.style.display = 'none';
            }, 3000);
        } else {
            typingIndicator.style.display = 'none';
        }
    }


    handleReadReceipt(data) {
        const {message_ids} = data;

        message_ids.forEach(id => {
            const msgEl = document.querySelector(`.message[data-id="${id}"]`);
            if (msgEl) {
                msgEl.classList.add('read');
                const readTick = msgEl.querySelector('.read-indicator');
                if (readTick) readTick.style.visibility = 'visible';
            }
        });
    }


    handleUserStatus(data) {
        const statusEl = document.querySelector('.user-status');
        if (!statusEl) return;

        if (data.online) {
            statusEl.textContent = 'Online';
            statusEl.style.color = 'green';
        } else {
            statusEl.textContent = 'Offline';
            statusEl.style.color = 'gray';
        }
    }
}
