# DataMind ChatBot 🤖

<div align="center">
  <img src="static/images/logo.png" alt="DataMind Logo" width="200"/>
  
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
  [![MongoDB Version](https://img.shields.io/badge/MongoDB-4.4%2B-green)](https://www.mongodb.com/)
  [![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)
</div>

## 📌 Aperçu du Projet

DataMind est un chatbot intelligent permettant d'interroger des bases MongoDB en langage naturel, avec intégration d'LLM pour les requêtes complexes.

### ✨ Fonctionnalités clés

- 💬 Interface conversationnelle intuitive
- 🛠️ Support des opérations CRUD via NLP
- 🔍 Analyse de données avec Groq/Ollama
- 📊 Exploration visuelle des schémas
- ⚡ Réponses rapides avec cache intelligent

## 🚀 Démarrage Rapide

### Prérequis

- Python 3.8+
- MongoDB 4.4+
- Compte Groq (optionnel pour LLM cloud)
- Clé API OpenAI (optionnelle)

### Installation

```bash
# Clonez le dépôt
git clone https://github.com/votre-repo/datamind-chatbot.git
cd datamind-chatbot

# Configurez l'environnement
cp .env.example .env
# Editez le fichier .env avec vos paramètres

# Installez les dépendances
pip install -r requirements.txt