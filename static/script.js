class ChatbotInterface {
    constructor() {
        this.currentDbType = 'mysql';
        this.initializeElements();
        this.attachEventListeners();
        this.loadDatabaseInfo();
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
    }

    onDatabaseTypeChange() {
        this.applyTheme();
        this.loadDatabaseInfo();
        this.updateCurrentDbType();
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
            this.tablesList.innerHTML = '<li>Chargement...</li>';
            this.currentDbNameSpan.textContent = 'Chargement...';

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
                this.currentDbNameSpan.textContent = data.db_name || 'Non disponible';
                this.updateTablesList(data.tables || []);
            } else {
                this.currentDbNameSpan.textContent = 'Erreur';
                this.tablesList.innerHTML = `<li style="color: #e74c3c;">Erreur: ${data.error}</li>`;
            }
        } catch (error) {
            console.error('Erreur lors du chargement des informations de la base de données:', error);
            this.currentDbNameSpan.textContent = 'Erreur de connexion';
            this.tablesList.innerHTML = '<li style="color: #e74c3c;">Erreur de connexion</li>';
        }
    }

    updateTablesList(tables) {
        if (tables.length === 0) {
            this.tablesList.innerHTML = '<li>Aucune table trouvée</li>';
            return;
        }

        this.tablesList.innerHTML = tables.map(table => 
            `<li>${table}</li>`
        ).join('');
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.sendButton.disabled = true;
        this.sendButton.textContent = 'Envoi...';

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: message,
                    db_type: this.currentDbType,
                    use_mock_data: false
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.addMessage(data.response, 'bot');
            } else {
                this.addMessage(`Erreur: ${data.error}`, 'bot');
            }
        } catch (error) {
            console.error('Erreur lors de l\'envoi du message:', error);
            this.addMessage('Erreur de connexion au serveur.', 'bot');
        } finally {
            this.sendButton.disabled = false;
            this.sendButton.textContent = 'Envoyer';
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
}

// Initialiser l'interface quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    new ChatbotInterface();
});

