import re
from typing import Dict, List, Any, Tuple, Optional

class NLPQueryProcessor:
    def __init__(self, database, language_model_processor):
        self.database = database
        self.llm = language_model_processor
        
        # Mots-clés pour différents types de requêtes
        self.intent_keywords = {
            'count': ['combien', 'nombre', 'count', 'total', 'quantité'],
            'list': ['liste', 'tous', 'toutes', 'all', 'show', 'affiche', 'donne', 'qui sont', 'quels sont', 'quelles sont', 'noms'],
            'search': ['trouve', 'cherche', 'search', 'find', 'où', 'with', 'contient'],
            'filter': ['filter', 'filtre', 'avec', 'ayant', 'having', 'where', 'de la catégorie', 'de categorie', 'catégorie', 'category'],
            'distinct': ['différent', 'unique', 'distinct', 'types', 'catégories', 'différentes'],
            # CORRECTION: Ajout de plus de mots-clés pour l'agrégation
            'aggregate': ['moyenne', 'somme', 'sum', 'average', 'max', 'min', 'group', 'prix moyen', 'mean']
        }
        
        # Opérateurs de comparaison
        self.comparison_ops = {
            'égal': '$eq', 'equal': '$eq', '=': '$eq',
            'supérieur': '$gt', 'greater': '$gt', '>': '$gt',
            'inférieur': '$lt', 'less': '$lt', '<': '$lt',
            'contient': '$regex', 'contains': '$regex', 'like': '$regex'
        }

        # Synonymes étendus pour les collections
        self.collection_synonyms = {
            'users': ['utilisateur', 'utilisateurs', 'user', 'users', 'personne', 'personnes', 'client', 'clients', 'membre', 'membres'],
            'products': ['produit', 'produits', 'product', 'products', 'article', 'articles', 'item', 'items', 'dproduit'],
            'orders': ['commande', 'commandes', 'order', 'orders', 'achat', 'achats', 'purchase', 'purchases'],
            'categories': ['catégorie', 'catégories', 'category', 'categories', 'type', 'types', 'classe', 'classes'],
            'companies': ['entreprise', 'entreprises', 'company', 'companies', 'société', 'sociétés', 'firm', 'firms'],
            'animals': ['animal', 'animaux', 'animals', 'bête', 'bêtes', 'pet', 'pets'],
            'books': ['livre', 'livres', 'book', 'books', 'ouvrage', 'ouvrages'],
            'employees': ['employé', 'employés', 'employee', 'employees', 'staff', 'personnel'],
            'students': ['étudiant', 'étudiants', 'student', 'students', 'élève', 'élèves'],
            'teachers': ['professeur', 'professeurs', 'teacher', 'teachers', 'enseignant', 'enseignants'],
            'courses': ['cours', 'course', 'courses', 'matière', 'matières', 'subject', 'subjects']
        }

    def detect_intent(self, query: str) -> str:
        """Détecter l'intention de la requête - CORRIGÉ"""
        query_lower = query.lower()
        
        # CORRECTION: Détecter spécifiquement les agrégations en premier
        if any(word in query_lower for word in ['moyenne', 'average', 'prix moyen', 'mean']):
            return 'aggregate'
        
        # Vérifier les intentions dans un ordre prioritaire
        intent_priority = ['distinct', 'count', 'aggregate', 'filter', 'search', 'list']
        
        for intent in intent_priority:
            keywords = self.intent_keywords[intent]
            if any(keyword in query_lower for keyword in keywords):
                # Cas spéciaux pour disambiguation
                if intent == 'filter' and any(word in query_lower for word in ['catégorie', 'category', 'avec', 'de la']):
                    return 'filter'
                elif intent == 'distinct' and any(word in query_lower for word in ['différentes', 'quelles sont les']):
                    return 'distinct'
                elif intent == 'aggregate' and any(word in query_lower for word in ['moyenne', 'average']):
                    return 'aggregate'
                return intent
        
        return 'list'  # Par défaut

    def extract_table_from_query(self, query: str, available_tables: List[str]) -> str:
        """Extraire la table la plus pertinente de la requête"""
        query_lower = query.lower()
        print(f"DEBUG: Recherche table dans '{query_lower}' parmi {available_tables}")
        
        # Recherche directe du nom de table
        for table in available_tables:
            if table.lower() in query_lower:
                print(f"DEBUG: Table trouvée directement: {table}")
                return table
        
        # Recherche par synonymes étendus
        for table in available_tables:
            table_lower = table.lower()
            
            # Chercher dans nos synonymes prédéfinis
            if table_lower in self.collection_synonyms:
                synonyms = self.collection_synonyms[table_lower]
                for synonym in synonyms:
                    if synonym in query_lower:
                        print(f"DEBUG: Table trouvée via synonyme '{synonym}': {table}")
                        return table
        
        # Recherche par mots-clés spécifiques contextuels
        keyword_mapping = {
            'prix': 'products',
            'price': 'products',
            'catégorie': 'products',
            'category': 'products',
            'marque': 'products',
            'brand': 'products',
            'stock': 'products',
            'âge': 'users',
            'age': 'users',
            'email': 'users',
            'nom': ['users', 'products'],  # Peut être les deux
            'name': ['users', 'products']
        }
        
        for keyword, table_candidates in keyword_mapping.items():
            if keyword in query_lower:
                if isinstance(table_candidates, list):
                    # Si plusieurs candidats, prendre le premier disponible
                    for candidate in table_candidates:
                        if candidate in available_tables:
                            print(f"DEBUG: Table trouvée via mot-clé '{keyword}': {candidate}")
                            return candidate
                else:
                    if table_candidates in available_tables:
                        print(f"DEBUG: Table trouvée via mot-clé '{keyword}': {table_candidates}")
                        return table_candidates
        
        # Recherche partielle améliorée
        words_in_query = [word for word in query_lower.split() if len(word) > 2]
        for word in words_in_query:
            for table in available_tables:
                if word in table.lower() or table.lower() in word:
                    print(f"DEBUG: Table trouvée partiellement '{word}': {table}")
                    return table
        
        print(f"DEBUG: Aucune table trouvée, utilisation par défaut: {available_tables[0] if available_tables else None}")
        return available_tables[0] if available_tables else None

    def extract_fields_from_query(self, query: str, available_fields: List[str]) -> List[str]:
        """Extraire les champs pertinents de la requête"""
        query_lower = query.lower()
        relevant_fields = []
        
        # CORRECTION: Pour les moyennes, identifier le champ à calculer
        if 'moyenne' in query_lower or 'average' in query_lower:
            if 'prix' in query_lower or 'price' in query_lower:
                price_fields = [f for f in available_fields if 'price' in f.lower() or 'prix' in f.lower()]
                if price_fields:
                    relevant_fields.extend(price_fields)
        
        # Si on demande spécifiquement les noms
        if any(word in query_lower for word in ['noms', 'nom', 'name', 'appelé', 'qui sont']):
            name_fields = [f for f in available_fields if 'name' in f.lower() or 'nom' in f.lower()]
            if name_fields:
                relevant_fields.extend(name_fields)
        
        # Recherche directe des noms de champs
        for field in available_fields:
            if field.lower() in query_lower:
                relevant_fields.append(field)
        
        # Recherche par synonymes étendus
        field_synonyms = {
            'name': ['nom', 'name', 'titre', 'label', 'appellation', 'désignation', 'noms'],
            'age': ['âge', 'age', 'années', 'ans'],
            'email': ['email', 'mail', 'courriel', 'e-mail'],
            'price': ['prix', 'price', 'coût', 'cost', 'tarif', 'montant'],
            'date': ['date', 'time', 'temps', 'moment', 'quand'],
            'status': ['statut', 'status', 'état', 'state', 'situation'],
            'address': ['adresse', 'address', 'lieu', 'location', 'localisation'],
            'city': ['ville', 'city', 'localité'],
            'country': ['pays', 'country', 'nation'],
            'category': ['catégorie', 'category', 'type', 'genre', 'categorie'],
            'brand': ['marque', 'brand', 'fabricant'],
            'stock': ['stock', 'quantité', 'disponibilité'],
            'description': ['description', 'détail', 'détails', 'info', 'informations']
        }
        
        for field in available_fields:
            field_lower = field.lower()
            for key, synonyms in field_synonyms.items():
                if key in field_lower:
                    if any(synonym in query_lower for synonym in synonyms):
                        if field not in relevant_fields:
                            relevant_fields.append(field)
        
        print(f"DEBUG: Champs pertinents trouvés: {relevant_fields}")
        return relevant_fields

    def extract_conditions(self, query: str) -> Dict[str, Any]:
        """Extraire les conditions de la requête"""
        conditions = {}
        query_lower = query.lower()
        print(f"DEBUG: Extraction conditions de '{query_lower}'")
        
        # Patterns pour l'âge
        age_patterns = [
            r'plus\s+de\s+(\d+)\s*ans?',
            r'plus\s+de\s+(\d+)\s*années?',
            r'supérieur\s+à\s+(\d+)\s*ans?',
            r'supérieur\s+à\s+(\d+)\s*années?',
            r'âge\s*>\s*(\d+)',
            r'age\s*>\s*(\d+)',
            r'âgés?\s+de\s+plus\s+de\s+(\d+)',
            r'(\d+)\s*ans?\s+et\s+plus',
            r'(\d+)\s*années?\s+et\s+plus'
        ]
        
        for pattern in age_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                value = int(match)
                conditions['age'] = {'$gt': value}
                print(f"DEBUG: Condition âge > {value} ajoutée")
                break
        
        # Patterns pour l'âge inférieur
        age_less_patterns = [
            r'moins\s+de\s+(\d+)\s*ans?',
            r'moins\s+de\s+(\d+)\s*années?',
            r'inférieur\s+à\s+(\d+)\s*ans?',
            r'âge\s*<\s*(\d+)',
            r'age\s*<\s*(\d+)'
        ]
        
        for pattern in age_less_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                value = int(match)
                conditions['age'] = {'$lt': value}
                print(f"DEBUG: Condition âge < {value} ajoutée")
                break
        
        # Patterns pour les catégories
        category_patterns = [
            r'catégorie\s*["\']?(\w+)["\']?',
            r'categorie\s*["\']?(\w+)["\']?',
            r'de\s+la\s+catégorie\s*["\']?(\w+)["\']?',
            r'de\s+categorie\s*["\']?(\w+)["\']?',
            r'avec\s+catégorie\s*["\']?(\w+)["\']?',
            r'category\s*["\']?(\w+)["\']?'
        ]
        
        for pattern in category_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                category_value = match.strip().capitalize()  # Normaliser
                conditions['category'] = {'$regex': category_value, '$options': 'i'}
                print(f"DEBUG: Condition catégorie '{category_value}' ajoutée")
                break
        
        # Patterns pour les noms/marques
        name_patterns = [
            r'nom\s*[=:]\s*["\']?([^"\']+)["\']?',
            r'avec\s*le\s*nom\s*["\']?([^"\']+)["\']?',
            r'appelés?\s*["\']?([^"\']+)["\']?',
            r'marque\s*["\']?([^"\']+)["\']?',
            r'brand\s*["\']?([^"\']+)["\']?'
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                value = match.strip()
                if 'marque' in pattern or 'brand' in pattern:
                    conditions['brand'] = {'$regex': value, '$options': 'i'}
                else:
                    conditions['name'] = {'$regex': value, '$options': 'i'}
                print(f"DEBUG: Condition nom/marque '{value}' ajoutée")
        
        # Patterns pour les prix
        price_patterns = [
            r'prix\s*[>=<]\s*(\d+)',
            r'price\s*[>=<]\s*(\d+)',
            r'coût\s*[>=<]\s*(\d+)',
            r'plus\s+de\s+(\d+)\s*euros?',
            r'moins\s+de\s+(\d+)\s*euros?'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                value = int(match)
                if 'plus de' in query_lower:
                    conditions['price'] = {'$gt': value}
                elif 'moins de' in query_lower:
                    conditions['price'] = {'$lt': value}
                else:
                    conditions['price'] = value
                print(f"DEBUG: Condition prix ajoutée: {conditions['price']}")
        
        print(f"DEBUG: Conditions finales: {conditions}")
        return conditions

    def build_mongodb_query(self, intent: str, conditions: Dict, fields: List[str]) -> Tuple[Dict, Optional[Dict]]:
        """Construire la requête MongoDB"""
        query = conditions.copy() if conditions else {}
        projection = None
        
        if intent == 'count':
            return query, None
        
        elif intent == 'distinct' and fields:
            return query, {'distinct': fields[0]}
        
        elif intent == 'aggregate':
            # CORRECTION: Pour les agrégations, on ne veut pas de projection spéciale ici
            return query, None
        
        elif intent == 'list':
            if fields:
                projection = {"_id": 0}
                for field in fields:
                    projection[field] = 1
            else:
                projection = {"_id": 0}  # Exclure _id par défaut
        
        elif intent == 'filter':
            # Pour les filtres, on veut tous les champs pertinents
            projection = {"_id": 0}
            if fields:
                for field in fields:
                    projection[field] = 1
        
        else:
            projection = {"_id": 0}
        
        print(f"DEBUG: Query MongoDB: {query}, Projection: {projection}")
        return query, projection

    def understand_query(self, query: str) -> Tuple[Optional[str], Optional[Dict], Optional[Dict], str]:
        """Analyser et comprendre la requête utilisateur"""
        try:
            print(f"DEBUG: Analyse de la requête: '{query}'")
            
            # Obtenir les tables disponibles
            tables = self.database.get_tables()
            if not tables:
                return None, {}, None, 'list'
            
            print(f"DEBUG: Tables disponibles: {tables}")
            
            # Détecter l'intention
            intent = self.detect_intent(query)
            print(f"DEBUG: Intention détectée: {intent}")
            
            # Extraire la table cible
            target_table = self.extract_table_from_query(query, tables)
            print(f"DEBUG: Table cible: {target_table}")
            
            if not target_table:
                return None, {}, None, intent
            
            # Obtenir les champs de la table
            available_fields = self.database.get_fields(target_table)
            print(f"DEBUG: Champs disponibles: {available_fields}")
            
            # Extraire les champs pertinents
            relevant_fields = self.extract_fields_from_query(query, available_fields)
            
            # Extraire les conditions
            conditions = self.extract_conditions(query)
            
            # Construire la requête MongoDB
            mongo_query, projection = self.build_mongodb_query(intent, conditions, relevant_fields)
            
            print(f"DEBUG: Résultat final - Table: {target_table}, Query: {mongo_query}, Projection: {projection}, Intent: {intent}")
            
            return target_table, mongo_query, projection, intent
            
        except Exception as e:
            print(f"Erreur dans understand_query: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, {}, None, 'list'

    def execute_query_based_on_intent(self, table: str, query: Dict, projection: Optional[Dict], intent: str) -> Any:
        """Exécuter la requête selon l'intention détectée - CORRIGÉ"""
        try:
            print(f"DEBUG: Exécution - Table: {table}, Query: {query}, Intent: {intent}")
            
            if intent == 'count':
                result = self.database.count_documents(table, query)
                print(f"DEBUG: Count result: {result}")
                return result
            
            elif intent == 'distinct' and projection and 'distinct' in projection:
                field = projection['distinct']
                result = self.database.get_distinct_values(table, field)
                print(f"DEBUG: Distinct result: {result}")
                return result
            
            elif intent == 'aggregate':
                # CORRECTION MAJEURE: Logique d'agrégation améliorée
                print(f"DEBUG: Traitement agrégation pour table: {table}")
                
                # Pipeline d'agrégation pour calculer la moyenne des prix
                pipeline = []
                
                # Ajouter le match si on a des conditions
                if query:
                    pipeline.append({"$match": query})
                
                # Ajouter l'agrégation pour la moyenne des prix
                pipeline.append({
                    "$group": {
                        "_id": None,
                        "average_price": {"$avg": "$price"},
                        "count": {"$sum": 1},
                        "total": {"$sum": "$price"},
                        "max_price": {"$max": "$price"},
                        "min_price": {"$min": "$price"}
                    }
                })
                
                print(f"DEBUG: Pipeline d'agrégation: {pipeline}")
                result = self.database.aggregate_query(table, pipeline)
                print(f"DEBUG: Aggregate result: {result}")
                return result
            
            else:
                result = self.database.execute_query(table, query, projection)
                print(f"DEBUG: Query result count: {len(result) if isinstance(result, list) else 'Non-list'}")
                if isinstance(result, list) and len(result) > 0:
                    print(f"DEBUG: First result: {result[0]}")
                return result
                
        except Exception as e:
            print(f"Erreur exécution requête: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def get_collection_display_name(self, collection_name: str) -> str:
        """Obtenir le nom d'affichage correct pour la collection"""
        collection_lower = collection_name.lower()
        
        display_names = {
            'users': 'utilisateurs',
            'products': 'produits', 
            'orders': 'commandes',
            'categories': 'catégories',
            'companies': 'entreprises',
            'animals': 'animaux',
            'books': 'livres',
            'employees': 'employés',
            'students': 'étudiants',
            'teachers': 'professeurs',
            'courses': 'cours'
        }
        
        for key, display_name in display_names.items():
            if key in collection_lower:
                return display_name
        
        # Si pas trouvé, retourner le nom original
        return collection_name