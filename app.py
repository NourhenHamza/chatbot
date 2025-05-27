from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from models.database import DynamicDatabase
from models.nlp_processor import NLPQueryProcessor
from models.llm_helpers import LanguageModelRequest
from dotenv import load_dotenv
import logging
import webbrowser
import threading
import time

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialisation des composants
db = DynamicDatabase()
language_model_processor = LanguageModelRequest()
nlp_processor = NLPQueryProcessor(db, language_model_processor)

def format_response_for_collection(data, collection_name, intent, query_conditions=None):
    """Formater la réponse selon la collection et l'intention - CORRIGÉ"""
    collection_display = nlp_processor.get_collection_display_name(collection_name)
    
    if intent == 'count':
        if query_conditions:
            return f"Il y a {data} {collection_display} correspondant aux critères spécifiés."
        else:
            return f"Il y a {data} {collection_display} au total."
    
    elif intent == 'list':
        if not data or len(data) == 0:
            return f"Aucun {collection_display[:-1]} trouvé."
        
        # Extraire les noms ou identifiants principaux
        items = []
        for item in data:
            if isinstance(item, dict):
                # Priorité pour trouver le champ de nom
                name_fields = ['name', 'nom', 'title', 'titre', 'label']
                name = None
                for field in name_fields:
                    if field in item:
                        name = item[field]
                        break
                
                if name:
                    items.append(str(name))
                elif 'id' in item:
                    items.append(f"{collection_display[:-1]} {item['id']}")
                else:
                    # Prendre la première valeur non-nulle
                    for value in item.values():
                        if value and str(value) not in ['None', 'null']:
                            items.append(str(value))
                            break
        
        if items:
            if len(items) <= 5:
                return f"Les {collection_display} sont : {', '.join(items)}"
            else:
                return f"Les {collection_display} sont : {', '.join(items[:5])} et {len(items)-5} autres"
        else:
            return f"Les {collection_display} ont été trouvés mais les noms ne sont pas disponibles."
    
    elif intent == 'distinct':
        if isinstance(data, list) and len(data) > 0:
            return f"Les valeurs distinctes sont : {', '.join(map(str, data))}"
        else:
            return f"Aucune valeur distincte trouvée."
    
    elif intent == 'aggregate':
        # CORRECTION MAJEURE: Meilleur formatage des résultats d'agrégation
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            result = data[0]  # Le premier (et généralement seul) résultat d'agrégation
            
            if 'average_price' in result and result['average_price'] is not None:
                avg_price = result['average_price']
                response_parts = [f"La moyenne des prix est : {avg_price:.2f}€"]
                
                # Ajouter des informations supplémentaires si disponibles
                if 'count' in result:
                    response_parts.append(f"(calculée sur {result['count']} {collection_display})")
                if 'min_price' in result and 'max_price' in result:
                    response_parts.append(f"Prix minimum : {result['min_price']}€, maximum : {result['max_price']}€")
                
                return " ".join(response_parts)
            
            elif 'sum' in result:
                return f"La somme est : {result['sum']}"
            elif 'max' in result:
                return f"La valeur maximale est : {result['max']}"
            elif 'min' in result:
                return f"La valeur minimale est : {result['min']}"
            else:
                # Cas générique pour autres agrégations
                formatted_result = {}
                for key, value in result.items():
                    if key != '_id' and value is not None:
                        if isinstance(value, float):
                            formatted_result[key] = f"{value:.2f}"
                        else:
                            formatted_result[key] = str(value)
                
                if formatted_result:
                    result_str = ", ".join([f"{k}: {v}" for k, v in formatted_result.items()])
                    return f"Résultat de l'agrégation : {result_str}"
        
        return f"Résultat de l'agrégation non disponible."
    
    return f"Informations sur les {collection_display} trouvées."

# Route pour servir l'interface frontend
@app.route("/")
def index():
    return render_template('index.html')

@app.route("/ask", methods=["POST"])
def ask():
    try:
        question = request.json.get("question")
        if not question:
            return jsonify({"error": "Question manquante"}), 400

        logger.info(f"Question reçue: {question}")

        # Analyser la requête
        target_table, mongo_query, projection, intent = nlp_processor.understand_query(question)
        
        if not target_table:
            available_collections = db.get_tables()
            return jsonify({
                "response": f"Je n'ai pas pu identifier de collection pertinente. Collections disponibles : {', '.join(available_collections)}",
                "intent": intent,
                "data_count": 0,
                "available_collections": available_collections
            })

        logger.info(f"Table: {target_table}, Intent: {intent}, Query: {mongo_query}, Projection: {projection}")

        # Exécuter la requête selon l'intention
        data = nlp_processor.execute_query_based_on_intent(target_table, mongo_query, projection, intent)
        
        logger.info(f"Données récupérées: {data} (type: {type(data)})")
        
        # Formatage de la réponse selon l'intention
        if intent == 'count':
            response = format_response_for_collection(data, target_table, intent, mongo_query)
            return jsonify({
                "response": response,
                "intent": intent,
                "collection": target_table,
                "count": data,
                "query_used": mongo_query
            })
        
        elif intent == 'distinct':
            response = format_response_for_collection(data, target_table, intent)
            return jsonify({
                "response": response,
                "intent": intent,
                "collection": target_table,
                "distinct_values": data,
                "data_count": len(data) if isinstance(data, list) else 0,
                "query_used": mongo_query
            })
        
        elif intent == 'aggregate':
            response = format_response_for_collection(data, target_table, intent)
            return jsonify({
                "response": response,
                "intent": intent,
                "collection": target_table,
                "aggregate_result": data,
                "query_used": mongo_query
            })
        
        elif intent == 'list' or intent == 'filter':
            response = format_response_for_collection(data, target_table, 'list', mongo_query)
            return jsonify({
                "response": response,
                "intent": intent,
                "collection": target_table,
                "data_count": len(data) if isinstance(data, list) else 0,
                "query_used": mongo_query,
                "projection_used": projection
            })
        
        # Pour les autres intentions ou cas génériques
        else:
            if isinstance(data, list) and len(data) > 0:
                # Vérifier si on a des conditions de filtrage pour éviter d'utiliser le LLM inutilement
                if mongo_query and len(mongo_query) > 0:
                    # On a des filtres, formatons simplement la réponse
                    response = format_response_for_collection(data, target_table, 'list', mongo_query)
                elif len(data) > 10 or any(len(str(item)) > 100 for item in data if isinstance(item, dict)):
                    # Utiliser le LLM seulement pour des analyses complexes
                    response = language_model_processor.ask_llm(question, data[:5])  # Limiter à 5 éléments
                else:
                    response = format_response_for_collection(data, target_table, 'list', mongo_query)
                
                return jsonify({
                    "response": response,
                    "intent": intent,
                    "collection": target_table,
                    "data_count": len(data),
                    "query_used": mongo_query
                })
            else:
                collection_display = nlp_processor.get_collection_display_name(target_table)
                if mongo_query and len(mongo_query) > 0:
                    response = f"Aucun {collection_display[:-1]} trouvé correspondant aux critères spécifiés."
                else:
                    response = f"Aucune donnée trouvée dans {collection_display}."
                
                return jsonify({
                    "response": response,
                    "intent": intent,
                    "collection": target_table,
                    "data_count": 0,
                    "query_used": mongo_query
                })

    except Exception as e:
        logger.error(f"Erreur dans /ask: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur du serveur: {str(e)}"}), 500

@app.route("/collections", methods=["GET"])
def get_collections():
    """Récupérer la liste des collections avec informations"""
    try:
        collections = db.get_tables()
        collections_info = []
        
        for collection in collections:
            fields = db.get_fields(collection)
            count = db.count_documents(collection)
            sample = db.get_sample_data(collection, 1)
            display_name = nlp_processor.get_collection_display_name(collection)
            
            collections_info.append({
                "name": collection,
                "display_name": display_name,
                "fields": fields,
                "document_count": count,
                "sample": sample[0] if sample else {}
            })
        
        return jsonify({"collections": collections_info})
    except Exception as e:
        logger.error(f"Erreur récupération collections: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/collections/<collection_name>/schema", methods=["GET"])
def get_collection_schema(collection_name):
    """Récupérer le schéma détaillé d'une collection"""
    try:
        fields = db.get_fields(collection_name)
        count = db.count_documents(collection_name)
        sample = db.get_sample_data(collection_name, 3)
        display_name = nlp_processor.get_collection_display_name(collection_name)
        
        # Analyser les types de données
        field_types = {}
        if sample:
            for doc in sample:
                for field, value in doc.items():
                    if field not in field_types:
                        field_types[field] = type(value).__name__
        
        return jsonify({
            "collection": collection_name,
            "display_name": display_name,
            "fields": fields,
            "field_types": field_types,
            "document_count": count,
            "sample_data": sample
        })
    except Exception as e:
        logger.error(f"Erreur schéma collection: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/search", methods=["POST"])
def search():
    """Recherche avancée dans une collection"""
    try:
        data = request.json
        collection = data.get("collection")
        search_term = data.get("search_term")
        fields = data.get("fields", [])
        
        if not collection or not search_term:
            return jsonify({"error": "Collection et terme de recherche requis"}), 400
        
        results = db.search_text(collection, search_term, fields if fields else None)
        collection_display = nlp_processor.get_collection_display_name(collection)
        
        return jsonify({
            "results": results,
            "count": len(results),
            "collection": collection,
            "collection_display": collection_display,
            "search_term": search_term
        })
    except Exception as e:
        logger.error(f"Erreur recherche: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/add_test_collection", methods=["POST"])
def add_test_collection():
    """Ajouter une collection de test (pour démonstration)"""
    try:
        data = request.json
        collection_name = data.get("collection_name")
        test_data = data.get("test_data", [])
        
        if not collection_name or not test_data:
            return jsonify({"error": "Nom de collection et données de test requis"}), 400
        
        # Insérer les données de test
        result = db.db[collection_name].insert_many(test_data)
        
        return jsonify({
            "message": f"Collection '{collection_name}' créée avec succès",
            "inserted_count": len(result.inserted_ids),
            "collection_display": nlp_processor.get_collection_display_name(collection_name)
        })
    except Exception as e:
        logger.error(f"Erreur création collection: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/debug/query", methods=["POST"])
def debug_query():
    """Route de debug pour tester les requêtes"""
    try:
        question = request.json.get("question")
        target_table, mongo_query, projection, intent = nlp_processor.understand_query(question)
        
        return jsonify({
            "question": question,
            "target_table": target_table,
            "mongo_query": mongo_query,
            "projection": projection,
            "intent": intent,
            "available_tables": db.get_tables(),
            "fields_in_table": db.get_fields(target_table) if target_table else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Vérification de santé avec info DB"""
    try:
        collections = db.get_tables()
        collections_info = {}
        for collection in collections:
            collections_info[collection] = {
                "display_name": nlp_processor.get_collection_display_name(collection),
                "count": db.count_documents(collection)
            }
        
        return jsonify({
            "status": "OK",
            "message": "Service en fonctionnement",
            "database_connected": True,
            "collections_count": len(collections),
            "collections": collections_info
        })
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "message": str(e),
            "database_connected": False
        }), 500

def open_browser():
    """Ouvrir le navigateur après un délai"""
    time.sleep(1.5)  # Attendre que le serveur soit prêt
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == "__main__":
    # Lancer l'ouverture du navigateur dans un thread séparé
    threading.Thread(target=open_browser, daemon=True).start()
    
    print("🚀 Utilisation de Groq API (gratuit)")
    print("🌐 Interface web disponible sur: http://127.0.0.1:5000")
    print("📱 Le navigateur va s'ouvrir automatiquement...")
    print("🔧 Route de debug disponible sur: http://127.0.0.1:5000/debug/query")
    
    app.run(debug=True, use_reloader=False)  # use_reloader=False évite le double lancement