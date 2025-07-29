from flask import Flask, request, jsonify
from flask_cors import CORS  # <-- Add this import
from models.database import DynamicDatabase
from models.nlp_processor import NLPQueryProcessor
from models.llm_helpers import LanguageModelRequest
from dotenv import load_dotenv
import os 
 

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Enable CORS for all routes and origins by default
CORS(app)  # <-- Add this line

db = DynamicDatabase()
language_model_processor = LanguageModelRequest()
nlp_processor = NLPQueryProcessor(db, language_model_processor)


@app.route("/ask", methods=["POST"])
def ask():
    question = request.json.get("question")
    use_mock_data = request.json.get("use_mock_data", False)
    db_type = request.json.get("db_type", os.environ.get("DATABASE_TYPE"))
    
    # Set database type and mock data flag
    db.db_type = db_type.lower()
    db.set_mock_data(use_mock_data)

    try:
        # Process the question
        table_name, field, target_query = nlp_processor.understand_query(question)
        
        if table_name:
            data = db.query(table_name, field, target_query)
            response = language_model_processor.ask_llm(question, data)
            return jsonify({"response": response})
            
        return jsonify({"response": f"Processed question: {question}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True)
