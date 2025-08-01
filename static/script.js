class ChatbotInterface {
    constructor() {
        this.currentDbType = 'mysql';
        this.currentConversationId = null;
        this.conversations = {};
        this.initializeElements();
        this.attachEventListeners();
        this.loadDatabaseInfo();
        this.loadConversations();
        this.applyTheme();
    }

    initializeElements() {
        this.dbTypeSelect = document.getElementById('dbType');
        this.currentDbTypeSpan = document.getElementById('currentDbType');
        this.currentDbNameSpan = document.getElementById('currentDbName');
        this.tablesList = document.getElementById('tablesList');
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        
        // New elements for conversations
        this.conversationsList = document.getElementById('conversationsList');
        this.newConversationBtn = document.getElementById('newConversationBtn');
        this.conversationTitle = document.getElementById('conversationTitle');
        this.editTitleBtn = document.getElementById('editTitleBtn');
        this.deleteConversationBtn = document.getElementById('deleteConversationBtn');
        
        // Modal elements
        this.editTitleModal = document.getElementById('editTitleModal');
        this.newTitleInput = document.getElementById('newTitleInput');
        this.saveTitleBtn = document.getElementById('saveTitleBtn');
        this.cancelTitleBtn = document.getElementById('cancelTitleBtn');
        
        this.deleteModal = document.getElementById('deleteModal');
        this.confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        this.cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    }

    attachEventListeners() {
        this.dbTypeSelect.addEventListener('change', (e) => {
            this.currentDbType = e.target.value;
            this.onDatabaseTypeChange();
        });

        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });

        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        // Conversation events
        this.newConversationBtn.addEventListener('click', () => {
            this.createNewConversation();
        });

        this.editTitleBtn.addEventListener('click', () => {
            this.showEditTitleModal();
        });

        this.deleteConversationBtn.addEventListener('click', () => {
            this.showDeleteModal();
        });

        // Modal events
        this.saveTitleBtn.addEventListener('click', () => {
            this.saveConversationTitle();
        });

        this.cancelTitleBtn.addEventListener('click', () => {
            this.hideEditTitleModal();
        });

        this.confirmDeleteBtn.addEventListener('click', () => {
            this.deleteCurrentConversation();
        });

        this.cancelDeleteBtn.addEventListener('click', () => {
            this.hideDeleteModal();
        });

        // Close modals when clicking outside
        this.editTitleModal.addEventListener('click', (e) => {
            if (e.target === this.editTitleModal) {
                this.hideEditTitleModal();
            }
        });

        this.deleteModal.addEventListener('click', (e) => {
            if (e.target === this.deleteModal) {
                this.hideDeleteModal();
            }
        });
    }

    onDatabaseTypeChange() {
        this.applyTheme();
        this.loadDatabaseInfo();
        this.loadConversations();
        this.updateCurrentDbType();
        this.currentConversationId = null;
        this.clearChatMessages();
        this.conversationTitle.textContent = 'Select a conversation';
    }

    applyTheme() {
        document.body.className = `theme-${this.currentDbType}`;
    }

    updateCurrentDbType() {
        const dbTypeNames = {
            'mysql': 'MySQL',
            'postgresql': 'PostgreSQL',
            'mongodb': 'MongoDB'
        };
        this.currentDbTypeSpan.textContent = dbTypeNames[this.currentDbType];
    }

    async loadDatabaseInfo() {
        try {
            this.tablesList.innerHTML = '<li>Loading...</li>';
            this.currentDbNameSpan.textContent = 'Loading...';

            const response = await fetch('/db_info', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    db_type: this.currentDbType
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.currentDbNameSpan.textContent = data.db_name || 'Not available';
                this.updateTablesList(data.tables || []);
            } else {
                this.currentDbNameSpan.textContent = 'Error';
                this.tablesList.innerHTML = `<li style="color: #e74c3c;">Error: ${data.error}</li>`;
            }
        } catch (error) {
            console.error('Error loading database information:', error);
            this.currentDbNameSpan.textContent = 'Connection error';
            this.tablesList.innerHTML = '<li style="color: #e74c3c;">Connection error</li>';
        }
    }

    updateTablesList(tables) {
        if (tables.length === 0) {
            this.tablesList.innerHTML = '<li>No tables found</li>';
            return;
        }

        this.tablesList.innerHTML = tables.map(table => 
            `<li>${table}</li>`
        ).join('');
    }

    async loadConversations() {
        try {
            this.conversationsList.innerHTML = '<div class="loading">Loading...</div>';

            const response = await fetch(`/conversations?db_type=${this.currentDbType}`);
            const data = await response.json();

            if (response.ok) {
                this.conversations[this.currentDbType] = data.conversations || [];
                this.updateConversationsList();
            } else {
                this.conversationsList.innerHTML = `<div class="error">Error: ${data.error}</div>`;
            }
        } catch (error) {
            console.error('Error loading conversations:', error);
            this.conversationsList.innerHTML = '<div class="error">Connection error</div>';
        }
    }

    updateConversationsList() {
        const conversations = this.conversations[this.currentDbType] || [];
        
        if (conversations.length === 0) {
            this.conversationsList.innerHTML = '<div class="no-conversations">No conversations</div>';
            return;
        }

        this.conversationsList.innerHTML = conversations.map(conv => 
            `<div class="conversation-item ${conv.id === this.currentConversationId ? 'active' : ''}" 
                 data-conversation-id="${conv.id}">
                <div class="conversation-title">${conv.title}</div>
                <div class="conversation-date">${this.formatDate(conv.updated_at)}</div>
            </div>`
        ).join('');

        // Add click events
        this.conversationsList.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', () => {
                const conversationId = item.dataset.conversationId;
                this.selectConversation(conversationId);
            });
        });
    }

    async createNewConversation() {
        try {
            const response = await fetch('/conversations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    db_type: this.currentDbType
                })
            });

            const data = await response.json();

            if (response.ok) {
                // Reload conversations list
                await this.loadConversations();
                // Select the new conversation
                this.selectConversation(data.conversation.id);
            } else {
                alert(`Error creating conversation: ${data.error}`);
            }
        } catch (error) {
            console.error('Error creating conversation:', error);
            alert('Connection error while creating conversation');
        }
    }

    async selectConversation(conversationId) {
        try {
            const response = await fetch(`/conversations/${conversationId}?db_type=${this.currentDbType}`);
            const data = await response.json();

            if (response.ok) {
                this.currentConversationId = conversationId;
                this.conversationTitle.textContent = data.conversation.title;
                this.loadConversationMessages(data.conversation.messages);
                this.updateConversationsList(); // Update visual selection
            } else {
                alert(`Error loading conversation: ${data.error}`);
            }
        } catch (error) {
            console.error('Error loading conversation:', error);
            alert('Connection error while loading conversation');
        }
    }

    loadConversationMessages(messages) {
        this.clearChatMessages();
        
        // Add welcome message
        this.addMessage('Hello! I\'m your assistant for querying the database. Ask me your questions!', 'bot');
        
        // Add all conversation messages
        messages.forEach(message => {
            this.addMessage(message.content, message.sender);
        });
    }

    clearChatMessages() {
        this.chatMessages.innerHTML = '';
    }

    showEditTitleModal() {
        if (!this.currentConversationId) return;
        
        this.newTitleInput.value = this.conversationTitle.textContent;
        this.editTitleModal.style.display = 'flex';
        this.newTitleInput.focus();
    }

    hideEditTitleModal() {
        this.editTitleModal.style.display = 'none';
        this.newTitleInput.value = '';
    }

    async saveConversationTitle() {
        const newTitle = this.newTitleInput.value.trim();
        if (!newTitle || !this.currentConversationId) return;

        try {
            const response = await fetch(`/conversations/${this.currentConversationId}/title`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    db_type: this.currentDbType,
                    title: newTitle
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.conversationTitle.textContent = newTitle;
                this.hideEditTitleModal();
                await this.loadConversations(); // Reload to update the list
            } else {
                alert(`Error updating title: ${data.error}`);
            }
        } catch (error) {
            console.error('Error updating title:', error);
            alert('Connection error while updating title');
        }
    }

    showDeleteModal() {
        if (!this.currentConversationId) return;
        this.deleteModal.style.display = 'flex';
    }

    hideDeleteModal() {
        this.deleteModal.style.display = 'none';
    }

    async deleteCurrentConversation() {
        if (!this.currentConversationId) return;

        try {
            const response = await fetch(`/conversations/${this.currentConversationId}?db_type=${this.currentDbType}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (response.ok) {
                this.hideDeleteModal();
                this.currentConversationId = null;
                this.conversationTitle.textContent = 'Select a conversation';
                this.clearChatMessages();
                this.addMessage('Hello! I\'m your assistant for querying the database. Ask me your questions!', 'bot');
                await this.loadConversations(); // Reload the list
            } else {
                alert(`Error deleting conversation: ${data.error}`);
            }
        } catch (error) {
            console.error('Error deleting conversation:', error);
            alert('Connection error while deleting conversation');
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.sendButton.disabled = true;
        this.sendButton.textContent = 'Sending...';

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: message,
                    db_type: this.currentDbType,
                    conversation_id: this.currentConversationId,
                    use_mock_data: false
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.addMessage(data.response, 'bot');
                
                // If it's a new conversation, update the ID and reload the list
                if (!this.currentConversationId && data.conversation_id) {
                    this.currentConversationId = data.conversation_id;
                    await this.loadConversations();
                    // Select the newly created conversation
                    const conversations = this.conversations[this.currentDbType] || [];
                    const newConv = conversations.find(c => c.id === data.conversation_id);
                    if (newConv) {
                        this.conversationTitle.textContent = newConv.title;
                        this.updateConversationsList();
                    }
                }
            } else {
                this.addMessage(`Error: ${data.error}`, 'bot');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('Server connection error.', 'bot');
        } finally {
            this.sendButton.disabled = false;
            this.sendButton.textContent = 'Send';
        }
    }

    addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        messageDiv.appendChild(messageContent);
        this.chatMessages.appendChild(messageDiv);
        
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays === 1) {
            return 'Today';
        } else if (diffDays === 2) {
            return 'Yesterday';
        } else if (diffDays <= 7) {
            return `${diffDays - 1} days ago`;
        } else {
            return date.toLocaleDateString('en-US');
        }
    }
}

// Initialize the interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatbotInterface();
});

