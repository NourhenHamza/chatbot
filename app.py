from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from models.database import DynamicDatabase
from models.nlp_processor import NLPQueryProcessor
from models.llm_helpers import LanguageModelRequest
from conversation_manager import ConversationManager
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Enable CORS for all routes and origins by default
CORS(app)

db = DynamicDatabase()
language_model_processor = LanguageModelRequest()
nlp_processor = NLPQueryProcessor(db, language_model_processor)
conversation_manager = ConversationManager()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    question = request.json.get("question")
    use_mock_data = request.json.get("use_mock_data", False)
    db_type = request.json.get("db_type", os.environ.get("DATABASE_TYPE"))
    conversation_id = request.json.get("conversation_id")
    
    print(f"DEBUG: Received question: '{question}'")
    print(f"DEBUG: use_mock_data: {use_mock_data}, db_type: {db_type}, conversation_id: {conversation_id}")
    
    # Vérifier si une conversation_id est fournie, sinon créer une nouvelle conversation
    if not conversation_id:
        conversation_id = conversation_manager.create_conversation(db_type)
        print(f"DEBUG: Created new conversation: {conversation_id}")
    
    # Ajouter le message de l'utilisateur à la conversation
    conversation_manager.add_message(db_type, conversation_id, question, "user")
    
    # Set database type and mock data flag
    db.db_type = db_type.lower()
    db.set_mock_data(use_mock_data)

    try:
        # Process the question
        table_name, field, target_query = nlp_processor.understand_query(question)
        print(f"DEBUG: NLP processor returned - table_name: '{table_name}', field: '{field}', target_query: '{target_query}'")
        
        if target_query == "SHOW_TABLES" or target_query == "SHOW_COLLECTIONS":
            data = db.query(None, None, target_query)
        else:
            data = db.query(table_name, field, target_query)

        print(f"DEBUG: Database query returned {len(data) if data else 0} rows")
            
        response = language_model_processor.ask_llm(question, data)
        print(f"DEBUG: LLM response: '{response[:100]}...' (truncated)")
        
        # Ajouter la réponse du bot à la conversation
        conversation_manager.add_message(db_type, conversation_id, response, "bot")
            
        return jsonify({"response": response, "conversation_id": conversation_id})
            
    except Exception as e:
        print(f"ERROR in ask endpoint: {str(e)}")
        error_message = f"Erreur: {str(e)}"
        # Ajouter le message d'erreur à la conversation
        conversation_manager.add_message(db_type, conversation_id, error_message, "bot")
        return jsonify({"error": str(e), "conversation_id": conversation_id}), 500

@app.route("/db_info", methods=["POST"])
def db_info():
    db_type = request.json.get("db_type")
    if not db_type:
        return jsonify({"error": "db_type is required"}), 400

    db.db_type = db_type.lower()
    db.set_mock_data(False) # Always use real data for db_info

    try:
        db_name = db.get_database_name()
        tables = db.get_tables()
        return jsonify({"db_name": db_name, "tables": tables})
    except Exception as e:
        print(f"ERROR in db_info endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Nouvelles routes pour la gestion des conversations

@app.route("/conversations", methods=["GET"])
def get_conversations():
    """Récupère toutes les conversations pour un type de base de données."""
    db_type = request.args.get("db_type")
    if not db_type:
        return jsonify({"error": "db_type is required"}), 400
    
    try:
        conversations = conversation_manager.get_conversations_by_type(db_type)
        return jsonify({"conversations": conversations})
    except Exception as e:
        print(f"ERROR in get_conversations endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/conversations", methods=["POST"])
def create_conversation():
    """Crée une nouvelle conversation."""
    data = request.json
    db_type = data.get("db_type")
    title = data.get("title")
    
    if not db_type:
        return jsonify({"error": "db_type is required"}), 400
    
    try:
        conversation_id = conversation_manager.create_conversation(db_type, title)
        conversation = conversation_manager.get_conversation(db_type, conversation_id)
        return jsonify({"conversation": conversation})
    except Exception as e:
        print(f"ERROR in create_conversation endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    """Récupère une conversation spécifique."""
    db_type = request.args.get("db_type")
    if not db_type:
        return jsonify({"error": "db_type is required"}), 400
    
    try:
        conversation = conversation_manager.get_conversation(db_type, conversation_id)
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404
        return jsonify({"conversation": conversation})
    except Exception as e:
        print(f"ERROR in get_conversation endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    """Supprime une conversation."""
    db_type = request.args.get("db_type")
    if not db_type:
        return jsonify({"error": "db_type is required"}), 400
    
    try:
        success = conversation_manager.delete_conversation(db_type, conversation_id)
        if not success:
            return jsonify({"error": "Conversation not found"}), 404
        return jsonify({"message": "Conversation deleted successfully"})
    except Exception as e:
        print(f"ERROR in delete_conversation endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/conversations/<conversation_id>/title", methods=["PUT"])
def update_conversation_title(conversation_id):
    """Met à jour le titre d'une conversation."""
    data = request.json
    db_type = data.get("db_type")
    new_title = data.get("title")
    
    if not db_type or not new_title:
        return jsonify({"error": "db_type and title are required"}), 400
    
    try:
        success = conversation_manager.update_conversation_title(db_type, conversation_id, new_title)
        if not success:
            return jsonify({"error": "Conversation not found"}), 404
        return jsonify({"message": "Title updated successfully"})
    except Exception as e:
        print(f"ERROR in update_conversation_title endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

