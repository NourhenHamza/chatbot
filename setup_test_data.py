#!/usr/bin/env python3
"""
Script pour créer des données de test dans MongoDB
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random

load_dotenv()

def setup_test_data():
    """Créer des données de test dans MongoDB"""
    try:
        # Connexion à MongoDB
        host = os.environ.get("MONGODB_HOST", "localhost")
        port = int(os.environ.get("MONGODB_PORT", "27017"))
        dbname = os.environ.get("MONGODB_DBNAME", "chatbot_db")
        
        client = MongoClient(f"mongodb://{host}:{port}/")
        db = client[dbname]
        
        print(f"✅ Connexion à MongoDB réussie!")
        print(f"Base de données: {dbname}")
        
        # Supprimer les collections existantes pour recommencer
        collections_to_create = ['users', 'products', 'orders', 'categories']
        for collection_name in collections_to_create:
            if collection_name in db.list_collection_names():
                db[collection_name].drop()
                print(f"🗑️  Collection '{collection_name}' supprimée")
        
        # Créer les catégories
        categories_data = [
            {"id": 1, "name": "Électronique", "description": "Appareils électroniques et accessoires"},
            {"id": 2, "name": "Vêtements", "description": "Vêtements et accessoires de mode"},
            {"id": 3, "name": "Maison", "description": "Articles pour la maison et le jardin"},
            {"id": 4, "name": "Sport", "description": "Équipements et vêtements de sport"},
            {"id": 5, "name": "Livres", "description": "Livres et magazines"}
        ]
        
        result = db.categories.insert_many(categories_data)
        print(f"📚 {len(result.inserted_ids)} catégories créées")
        
        # Créer les utilisateurs
        users_data = [
            {"id": 1, "name": "Alice Martin", "age": 25, "email": "alice.martin@email.com", 
             "city": "Paris", "country": "France", "joined_date": "2023-01-15"},
            {"id": 2, "name": "Bob Dupont", "age": 30, "email": "bob.dupont@email.com", 
             "city": "Lyon", "country": "France", "joined_date": "2023-02-20"},
            {"id": 3, "name": "Charlie Moreau", "age": 35, "email": "charlie.moreau@email.com", 
             "city": "Marseille", "country": "France", "joined_date": "2023-03-10"},
            {"id": 4, "name": "Diana Silva", "age": 28, "email": "diana.silva@email.com", 
             "city": "Toulouse", "country": "France", "joined_date": "2023-04-05"},
            {"id": 5, "name": "Étienne Bernard", "age": 42, "email": "etienne.bernard@email.com", 
             "city": "Nice", "country": "France", "joined_date": "2023-05-12"},
            {"id": 6, "name": "Fatima Benali", "age": 26, "email": "fatima.benali@email.com", 
             "city": "Strasbourg", "country": "France", "joined_date": "2023-06-18"},
        ]
        
        result = db.users.insert_many(users_data)
        print(f"👥 {len(result.inserted_ids)} utilisateurs créés")
        
        # Créer les produits
        products_data = [
            {"id": 1, "name": "MacBook Pro", "price": 2399, "category": "Électronique", 
             "stock": 15, "brand": "Apple", "description": "Ordinateur portable haut de gamme"},
            {"id": 2, "name": "iPhone 15", "price": 1199, "category": "Électronique", 
             "stock": 25, "brand": "Apple", "description": "Smartphone dernière génération"},
            {"id": 3, "name": "Samsung Galaxy S24", "price": 999, "category": "Électronique", 
             "stock": 30, "brand": "Samsung", "description": "Smartphone Android premium"},
            {"id": 4, "name": "Nike Air Max", "price": 159, "category": "Sport", 
             "stock": 50, "brand": "Nike", "description": "Chaussures de sport confortables"},
            {"id": 5, "name": "Adidas Ultraboost", "price": 179, "category": "Sport", 
             "stock": 40, "brand": "Adidas", "description": "Chaussures de running performantes"},
            {"id": 6, "name": "T-shirt Coton Bio", "price": 25, "category": "Vêtements", 
             "stock": 100, "brand": "EcoFashion", "description": "T-shirt en coton biologique"},
            {"id": 7, "name": "Jean Slim", "price": 89, "category": "Vêtements", 
             "stock": 75, "brand": "LeviStyle", "description": "Jean coupe slim moderne"},
            {"id": 8, "name": "Casque Bluetooth", "price": 299, "category": "Électronique", 
             "stock": 20, "brand": "Sony", "description": "Casque sans fil à réduction de bruit"},
            {"id": 9, "name": "Livre Python", "price": 45, "category": "Livres", 
             "stock": 200, "brand": "TechBooks", "description": "Guide complet de programmation Python"},
            {"id": 10, "name": "Lampe LED", "price": 35, "category": "Maison", 
             "stock": 60, "brand": "HomeLight", "description": "Lampe LED économique et design"}
        ]
        
        result = db.products.insert_many(products_data)
        print(f"🛍️  {len(result.inserted_ids)} produits créés")
        
        # Créer les commandes
        orders_data = []
        base_date = datetime.now() - timedelta(days=90)
        
        for i in range(1, 21):  # 20 commandes
            order_date = base_date + timedelta(days=random.randint(0, 90))
            user_id = random.randint(1, 6)
            product_id = random.randint(1, 10)
            quantity = random.randint(1, 3)
            
            # Trouver le prix du produit
            product = next((p for p in products_data if p["id"] == product_id), None)
            unit_price = product["price"] if product else 100
            total = unit_price * quantity
            
            orders_data.append({
                "id": i,
                "user_id": user_id,
                "product_id": product_id,
                "product_name": product["name"] if product else f"Produit {product_id}",
                "quantity": quantity,
                "unit_price": unit_price,
                "total": total,
                "order_date": order_date.strftime("%Y-%m-%d"),
                "status": random.choice(["pending", "shipped", "delivered", "cancelled"])
            })
        
        result = db.orders.insert_many(orders_data)
        print(f"📦 {len(result.inserted_ids)} commandes créées")
        
        # Statistiques finales
        print(f"\n📊 STATISTIQUES DE LA BASE DE DONNÉES:")
        for collection_name in collections_to_create:
            count = db[collection_name].count_documents({})
            print(f"  - {collection_name}: {count} documents")
        
        print(f"\n✅ Données de test créées avec succès!")
        print(f"Vous pouvez maintenant tester le chatbot avec des questions comme:")
        print(f"  - 'Combien d'utilisateurs?'")
        print(f"  - 'Liste tous les produits'")
        print(f"  - 'Utilisateurs de plus de 30 ans'")
        print(f"  - 'Produits de la catégorie Électronique'")
        print(f"  - 'Commandes en attente'")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des données: {str(e)}")

if __name__ == "__main__":
    print("🔧 Configuration des données de test pour le chatbot MongoDB")
    setup_test_data()