# test_mongo.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['chatbot_db']
    
    # Test de connexion
    client.admin.command('ping')
    print("✅ Connexion MongoDB réussie!")
    
    # Lister les collections
    collections = db.list_collection_names()
    print(f"📁 Collections disponibles: {collections}")
    
    # Tester une requête
    users = list(db.users.find({}, {"_id": 0}))
    print(f"👥 Utilisateurs: {users}")
    
except Exception as e:
    print(f"❌ Erreur de connexion: {e}")