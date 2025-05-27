import os
import re
from pymongo import MongoClient
from pymongo.database import Database
from typing import Optional, List, Dict, Union, Any
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamicDatabase:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None

    def connect(self):
        if self.client:
            return

        try:
            host = os.environ.get("MONGODB_HOST", "localhost")
            port = int(os.environ.get("MONGODB_PORT", "27017"))
            dbname = os.environ.get("MONGODB_DBNAME", "chatbot_db")

            connection_string = f"mongodb://{host}:{port}/"
            logger.info(f"Connexion à MongoDB: {connection_string}")
            
            self.client = MongoClient(connection_string)
            self.db = self.client[dbname]
            self.client.admin.command("ping")
            logger.info("✅ Connexion MongoDB réussie!")

        except Exception as e:
            logger.error(f"❌ Erreur de connexion MongoDB: {str(e)}")
            raise ConnectionError("Connexion à MongoDB échouée")

    def get_tables(self) -> List[str]:
        if self.db is None:
            self.connect()
        return self.db.list_collection_names()

    def get_fields(self, table_name: str) -> List[str]:
        if self.db is None:
            self.connect()

        # Analyser plusieurs documents pour obtenir tous les champs possibles
        pipeline = [
            {"$limit": 100},  # Limiter pour performance
            {"$project": {"arrayofkeyvalue": {"$objectToArray": "$$ROOT"}}},
            {"$unwind": "$arrayofkeyvalue"},
            {"$group": {"_id": None, "allkeys": {"$addToSet": "$arrayofkeyvalue.k"}}},
            {"$project": {"_id": 0, "allkeys": 1}}
        ]
        
        try:
            result = list(self.db[table_name].aggregate(pipeline))
            if result and 'allkeys' in result[0]:
                fields = result[0]['allkeys']
                # Filtrer le champ _id
                if '_id' in fields:
                    fields.remove('_id')
                return sorted(fields)
        except Exception as e:
            logger.warning(f"Erreur agrégation pour {table_name}: {e}")
        
        # Fallback: utiliser findOne
        doc = self.db[table_name].find_one()
        if doc:
            fields = list(doc.keys())
            if '_id' in fields:
                fields.remove('_id')
            return fields
        return []

    def get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict]:
        """Récupérer quelques exemples de données pour comprendre la structure"""
        if self.db is None:
            self.connect()
        
        try:
            return list(self.db[table_name].find({}, {"_id": 0}).limit(limit))
        except Exception as e:
            logger.error(f"Erreur échantillonnage {table_name}: {e}")
            return []

    def execute_query(self, table_name: str, query_dict: Dict, projection: Optional[Dict] = None) -> List[Dict]:
        """Exécuter une requête MongoDB personnalisée"""
        if self.db is None:
            self.connect()

        try:
            collection = self.db[table_name]
            
            if projection is None:
                projection = {"_id": 0}
            
            result = list(collection.find(query_dict, projection))
            logger.info(f"Requête exécutée sur {table_name}: {len(result)} résultats")
            return result
            
        except Exception as e:
            logger.error(f"Erreur requête sur {table_name}: {str(e)}")
            return []

    def count_documents(self, table_name: str, query_dict: Dict = None) -> int:
        """Compter les documents dans une collection"""
        if self.db is None:
            self.connect()
        
        try:
            if query_dict is None:
                query_dict = {}
            return self.db[table_name].count_documents(query_dict)
        except Exception as e:
            logger.error(f"Erreur count sur {table_name}: {e}")
            return 0

    def get_distinct_values(self, table_name: str, field: str) -> List[Any]:
        """Récupérer les valeurs distinctes d'un champ"""
        if self.db is None:
            self.connect()
        
        try:
            return self.db[table_name].distinct(field)
        except Exception as e:
            logger.error(f"Erreur distinct sur {table_name}.{field}: {e}")
            return []

    def aggregate_query(self, table_name: str, pipeline: List[Dict]) -> List[Dict]:
        """Exécuter une requête d'agrégation"""
        if self.db is None:
            self.connect()
        
        try:
            return list(self.db[table_name].aggregate(pipeline))
        except Exception as e:
            logger.error(f"Erreur agrégation sur {table_name}: {e}")
            return []

    def search_text(self, table_name: str, search_term: str, fields: List[str] = None) -> List[Dict]:
        """Recherche textuelle dans les champs spécifiés"""
        if self.db is None:
            self.connect()
        
        try:
            if fields is None:
                # Recherche dans tous les champs texte
                query = {"$text": {"$search": search_term}}
            else:
                # Recherche dans des champs spécifiques
                query = {"$or": []}
                for field in fields:
                    query["$or"].append({field: {"$regex": search_term, "$options": "i"}})
            
            return list(self.db[table_name].find(query, {"_id": 0}))
        except Exception as e:
            logger.error(f"Erreur recherche texte sur {table_name}: {e}")
            return []