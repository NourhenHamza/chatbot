from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from models.database import DynamicDatabase
from models.nlp_processor import NLPQueryProcessor
from models.llm_helpers import LanguageModelRequest
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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    question = request.json.get("question")
    use_mock_data = request.json.get("use_mock_data", False)
    db_type = request.json.get("db_type", os.environ.get("DATABASE_TYPE"))
    
    print(f"DEBUG: Received question: '{question}'")
    print(f"DEBUG: use_mock_data: {use_mock_data}, db_type: {db_type}")
    
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
            
        return jsonify({"response": response})
            
    except Exception as e:
        print(f"ERROR in ask endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

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

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

