import os
import requests
import json
from typing import List, Dict, Any
from langchain.schema import BaseOutputParser
from langchain.docstore.document import Document


class CommaSeparatedListOutputParser(BaseOutputParser):
    """Parse the output of an LLM call to a comma-separated list."""

    def parse(self, text: str):
        """Parse the output of an LLM call."""
        return text.strip().split(", ")


def convert_to_documents(data_list):
    data = []
    for data_dict in data_list:
        if isinstance(data_dict, dict):
            list_value = list(data_dict.keys())[0] if data_dict.keys() else "data"
            metadata = data_dict
            content = str(data_dict.get(list_value, data_dict))
            data.append(Document(page_content=content, metadata=metadata))
        else:
            data.append(Document(page_content=str(data_dict), metadata={}))
    return data


class LlamaLanguageModelRequest:
    """
    Classe pour utiliser Llama via Ollama (local) ou via API Groq (gratuit)
    """

    def __init__(self):
        # Configuration pour Ollama local
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'llama2')
        
        # Configuration pour Groq (API gratuite)
        self.groq_api_key = os.getenv('GROQ_API_KEY', '')
        self.groq_model = os.getenv('GROQ_MODEL', 'llama2-70b-4096')
        
        # Prompts système
        self.system_prompt = os.getenv('SYSTEM_PROMPT', "You are an AI assistant that provides information from given data. Be concise and helpful.")
        self.system_prompt_query = os.getenv('SYSTEM_PROMPT_QUERY', 
            "You are an AI that creates database queries based on user questions and database schema. "
            "Only respond with the query, no extra text.")
        
        # Détecter quelle méthode utiliser
        self.use_groq = bool(self.groq_api_key)
        self.use_ollama = self._check_ollama_available()
        
        if not self.use_groq and not self.use_ollama:
            print("⚠️  Ni Groq ni Ollama détecté. Utilisation du mode fallback.")
        elif self.use_groq:
            print("🚀 Utilisation de Groq API (gratuit)")
        elif self.use_ollama:
            print("🦙 Utilisation d'Ollama local")

    def _check_ollama_available(self) -> bool:
        """Vérifier si Ollama est disponible localement"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def _call_ollama(self, prompt: str, system_prompt: str = "") -> str:
        """Appeler Ollama localement"""
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                return f"Erreur Ollama: {response.status_code}"
                
        except Exception as e:
            return f"Erreur de connexion Ollama: {str(e)}"

    def _call_groq(self, prompt: str, system_prompt: str = "") -> str:
        """Appeler l'API Groq (gratuite)"""
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.groq_model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"Erreur Groq: {response.status_code}"
                
        except Exception as e:
            return f"Erreur de connexion Groq: {str(e)}"

    def _fallback_response(self, question: str, data_list: List[Dict]) -> str:
        """Réponse de secours si aucune API n'est disponible"""
        question_lower = question.lower()
        
        if not data_list:
            return "Aucune donnée trouvée pour répondre à votre question."
        
        # Réponses basiques selon le type de question
        if any(word in question_lower for word in ["qui", "utilisateurs", "users", "personnes"]):
            if isinstance(data_list, list) and len(data_list) > 0:
                names = []
                for user in data_list:
                    if isinstance(user, dict):
                        if 'name' in user:
                            names.append(user['name'])
                        elif 'nom' in user:
                            names.append(user['nom'])
                
                if names:
                    return f"Les utilisateurs sont : {', '.join(names)}"
                else:
                    return f"J'ai trouvé {len(data_list)} utilisateurs dans la base de données."
        
        elif any(word in question_lower for word in ["combien", "nombre", "count"]):
            return f"Il y a {len(data_list)} éléments dans les données."
        
        elif any(word in question_lower for word in ["âge", "age"]):
            ages = []
            for user in data_list:
                if isinstance(user, dict) and 'age' in user:
                    ages.append(str(user['age']))
            
            if ages:
                return f"Les âges sont : {', '.join(ages)} ans"
        
        # Réponse générique
        return f"Voici les données trouvées : {str(data_list)[:200]}..."

    def ask_llm(self, question: str, data_list: List[Dict]) -> str:
        """
        Poser une question au LLM avec les données
        """
        if not data_list:
            return "Aucune donnée disponible pour répondre à votre question."
        
        # Préparer le prompt
        data_str = json.dumps(data_list, ensure_ascii=False, indent=2)[:1000]  # Limiter la taille
        prompt = f"""Question: {question}

Données disponibles:
{data_str}

Réponds à la question en utilisant uniquement les données fournies. Sois concis et précis."""

        # Essayer les différentes méthodes
        if self.use_groq:
            response = self._call_groq(prompt, self.system_prompt)
            if not response.startswith("Erreur"):
                return response
        
        if self.use_ollama:
            response = self._call_ollama(prompt, self.system_prompt)
            if not response.startswith("Erreur"):
                return response
        
        # Fallback
        return self._fallback_response(question, data_list)

    def get_table_based_on_query(self, tables: List[str], query: str) -> List[str]:
        """Déterminer quelles tables utiliser selon la requête"""
        prompt = f"""Tables disponibles: {', '.join(tables)}
Question: {query}

Quelle(s) table(s) sont pertinente(s) pour cette question? Réponds uniquement avec le(s) nom(s) de table(s), séparés par des virgules."""

        if self.use_groq:
            response = self._call_groq(prompt)
            if not response.startswith("Erreur"):
                return [t.strip() for t in response.split(',')]
        
        if self.use_ollama:
            response = self._call_ollama(prompt)
            if not response.startswith("Erreur"):
                return [t.strip() for t in response.split(',')]
        
        # Fallback simple
        query_lower = query.lower()
        relevant_tables = []
        for table in tables:
            if table.lower() in query_lower or any(word in query_lower for word in ["utilisateur", "user"] if "user" in table.lower()):
                relevant_tables.append(table)
        
        return relevant_tables if relevant_tables else [tables[0]] if tables else []

    def get_column_based_on_query(self, columns: List[str], query: str) -> str:
        """Déterminer quelles colonnes utiliser selon la requête"""
        prompt = f"""Colonnes disponibles: {', '.join(columns)}
Question: {query}

Quelle colonne est la plus pertinente pour cette question? Réponds uniquement avec le nom de la colonne."""

        if self.use_groq:
            response = self._call_groq(prompt)
            if not response.startswith("Erreur"):
                return response.strip()
        
        if self.use_ollama:
            response = self._call_ollama(prompt)
            if not response.startswith("Erreur"):
                return response.strip()
        
        # Fallback simple
        query_lower = query.lower()
        for col in columns:
            if col.lower() in query_lower:
                return col
        
        return columns[0] if columns else ""

    def generate_query_by_llm(self, tables: List[str], columns: List[List[str]], query: str) -> str:
        """Générer une requête de base de données"""
        prompt = f"""Tables: {tables}
Colonnes: {columns}
Question: {query}

Génère une requête MongoDB appropriée pour cette question. Réponds uniquement avec la requête, pas d'explication."""

        if self.use_groq:
            response = self._call_groq(prompt, self.system_prompt_query)
            if not response.startswith("Erreur"):
                return response.strip()
        
        if self.use_ollama:
            response = self._call_ollama(prompt, self.system_prompt_query)
            if not response.startswith("Erreur"):
                return response.strip()
        
        # Fallback simple
        return "{}"  # Requête MongoDB vide pour récupérer tout


# Alias pour compatibilité
LanguageModelRequest = LlamaLanguageModelRequest