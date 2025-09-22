import os
import json
from datetime import datetime
from typing import List, Dict, Optional
import uuid

class ConversationManager:
    """Gestionnaire des conversations pour le chatbot avec support de différents types de BD."""
    
    def __init__(self, storage_file: str = "conversations.json"):
        """
        Initialise le gestionnaire de conversations.
        
        Args:
            storage_file: Fichier JSON pour stocker les conversations localement
        """
        self.storage_file = storage_file
        self.conversations = self._load_conversations()
    
    def _load_conversations(self) -> Dict:
        """Charge les conversations depuis le fichier de stockage."""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement des conversations: {e}")
        
        # Structure par défaut si le fichier n'existe pas ou est corrompu
        return {
            "mysql": {},
            "postgresql": {},
            "mongodb": {}
        }
    
    def _save_conversations(self):
        """Sauvegarde les conversations dans le fichier de stockage."""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des conversations: {e}")
    
    def create_conversation(self, db_type: str, title: str = None) -> str:
        """
        Crée une nouvelle conversation pour un type de base de données.
        
        Args:
            db_type: Type de base de données (mysql, postgresql, mongodb)
            title: Titre optionnel de la conversation
            
        Returns:
            ID de la conversation créée
        """
        if db_type not in ["mysql", "postgresql", "mongodb"]:
            raise ValueError(f"Type de base de données non supporté: {db_type}")
        
        conversation_id = str(uuid.uuid4())
        
        if title is None:
            title = f"Conversation {db_type.upper()} - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        conversation = {
            "id": conversation_id,
            "title": title,
            "db_type": db_type,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": []
        }
        
        self.conversations[db_type][conversation_id] = conversation
        self._save_conversations()
        
        return conversation_id
    
    def get_conversations_by_type(self, db_type: str) -> List[Dict]:
        """
        Récupère toutes les conversations pour un type de base de données.
        
        Args:
            db_type: Type de base de données
            
        Returns:
            Liste des conversations triées par date de mise à jour (plus récente en premier)
        """
        if db_type not in self.conversations:
            return []
        
        conversations = list(self.conversations[db_type].values())
        # Trier par date de mise à jour (plus récente en premier)
        conversations.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        
        return conversations
    
    def get_conversation(self, db_type: str, conversation_id: str) -> Optional[Dict]:
        """
        Récupère une conversation spécifique.
        
        Args:
            db_type: Type de base de données
            conversation_id: ID de la conversation
            
        Returns:
            Dictionnaire de la conversation ou None si non trouvée
        """
        return self.conversations.get(db_type, {}).get(conversation_id)
    
    def add_message(self, db_type: str, conversation_id: str, message: str, sender: str = "user") -> bool:
        """
        Ajoute un message à une conversation.
        
        Args:
            db_type: Type de base de données
            conversation_id: ID de la conversation
            message: Contenu du message
            sender: Expéditeur du message ("user" ou "bot")
            
        Returns:
            True si le message a été ajouté avec succès, False sinon
        """
        conversation = self.get_conversation(db_type, conversation_id)
        if not conversation:
            return False
        
        message_data = {
            "id": str(uuid.uuid4()),
            "content": message,
            "sender": sender,
            "timestamp": datetime.now().isoformat()
        }
        
        conversation["messages"].append(message_data)
        conversation["updated_at"] = datetime.now().isoformat()
        
        self._save_conversations()
        return True
    
    def delete_conversation(self, db_type: str, conversation_id: str) -> bool:
        """
        Supprime une conversation.
        
        Args:
            db_type: Type de base de données
            conversation_id: ID de la conversation
            
        Returns:
            True si la conversation a été supprimée avec succès, False sinon
        """
        if db_type in self.conversations and conversation_id in self.conversations[db_type]:
            del self.conversations[db_type][conversation_id]
            self._save_conversations()
            return True
        return False
    
    def update_conversation_title(self, db_type: str, conversation_id: str, new_title: str) -> bool:
        """
        Met à jour le titre d'une conversation.
        
        Args:
            db_type: Type de base de données
            conversation_id: ID de la conversation
            new_title: Nouveau titre
            
        Returns:
            True si le titre a été mis à jour avec succès, False sinon
        """
        conversation = self.get_conversation(db_type, conversation_id)
        if not conversation:
            return False
        
        conversation["title"] = new_title
        conversation["updated_at"] = datetime.now().isoformat()
        
        self._save_conversations()
        return True
    
    def auto_update_conversation_title(self, db_type: str, conversation_id: str, llm_processor) -> bool:
        """
        Met à jour automatiquement le titre d'une conversation basé sur son contenu.
        
        Args:
            db_type: Type de base de données
            conversation_id: ID de la conversation
            llm_processor: Instance du processeur LLM pour générer le titre
            
        Returns:
            True si le titre a été mis à jour avec succès, False sinon
        """
        conversation = self.get_conversation(db_type, conversation_id)
        if not conversation:
            return False
        
        messages = conversation.get("messages", [])
        if len(messages) < 2:  # Attendre au moins 2 messages (1 user + 1 bot)
            return False
        
        # Ne mettre à jour que si le titre est encore le titre par défaut
        current_title = conversation.get("title", "")
        if not current_title.startswith("Conversation") and not current_title.startswith("Nouvelle"):
            return False  # Le titre a déjà été personnalisé
        
        try:
            new_title = llm_processor.generate_conversation_title(messages)
            return self.update_conversation_title(db_type, conversation_id, new_title)
        except Exception as e:
            print(f"Erreur lors de la mise à jour automatique du titre: {e}")
            return False

    def get_conversation_messages(self, db_type: str, conversation_id: str) -> List[Dict]:
        """
        Récupère tous les messages d'une conversation.
        
        Args:
            db_type: Type de base de données
            conversation_id: ID de la conversation
            
        Returns:
            Liste des messages de la conversation
        """
        conversation = self.get_conversation(db_type, conversation_id)
        if not conversation:
            return []
        
        return conversation.get("messages", [])

