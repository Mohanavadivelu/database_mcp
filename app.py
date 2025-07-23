# app.py
# Flask web interface for the database querying system
# This file provides a web interface while the MCP server (mcp_server.py) provides protocol access

import os
import sqlite3
import json
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

# Import our shared database query engine
from database_tools import DatabaseQueryEngine, process_database_query

# --- 1. CONFIGURATION ---
# Load environment variables from .env file if present
load_dotenv()

DATABASE = 'usage.db'

# --- 2. FLASK APPLICATION SETUP ---
app = Flask(__name__)

# Initialize database query engine for web interface
try:
    db_engine = DatabaseQueryEngine()
    print("✅ Flask app initialized with database query engine")
except Exception as e:
    print(f"❌ Failed to initialize database engine: {e}")
    db_engine = None

# --- 3. HELPER FUNCTIONS ---
def get_db_connection():
    """Legacy helper function for backward compatibility."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# --- 4. API ENDPOINTS ---
@app.route('/api/llm_query', methods=['POST'])
def llm_query():
    """
    Flask API endpoint that converts natural language questions into SQL queries,
    executes them, and returns human-readable answers using the shared database engine.
    
    This endpoint now uses the shared DatabaseQueryEngine for MCP compliance.
    """
    
    # Check if database engine is available
    if not db_engine:
        return jsonify({'error': 'Database engine not initialized. Check OpenAI API key configuration.'}), 500
    
    # Step 1: INPUT VALIDATION
    print("🔍 Step 1: Validating input...")
    
    # 1.1: Ensure request is valid JSON
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    # 1.2: Extract and validate the user question
    user_question = request.json.get('question', '').strip()
    if not user_question:
        return jsonify({'error': 'No question provided'}), 400

    try:
        # Step 2: PROCESS QUERY USING SHARED ENGINE
        print("� Step 2: Processing query using shared database engine...")
        
        # Use the shared database query engine
        result = db_engine.process_natural_language_query(user_question)
        
        # Step 3: RETURN FLASK-COMPATIBLE RESPONSE
        print("✅ Step 3: Returning Flask-compatible response...")
        return jsonify({
            'answer': result['answer'],           # Human-readable response
            'data': result['data'],               # Raw data for charts/export
            'question': result['question'],       # Echo back the original question
            'sql': result.get('sql', '')          # Include generated SQL for debugging
        })

    # Step 4: ERROR HANDLING
    except ValueError as e:
        # Handle validation and security errors
        print(f"❌ Validation error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        # Handle all other errors
        print(f"❌ General error: {e}")
        error_message = f"An internal server error occurred: {e}"
        return jsonify({'answer': error_message}), 500

# --- 5. FRONTEND ROUTE ---
@app.route('/')
def index():
    return render_template('index.html')

# --- 6. MAIN EXECUTION BLOCK ---
if __name__ == '__main__':
    import database
    import document.populate_database as populate_database

    print("Initializing database...")
    database.init_db()

    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(id) FROM usage_data").fetchone()[0]
    conn.close()

    if count < 100:
        print("Database appears to be empty or sparse. Populating with realistic test data...")
        populate_database.main()
    else:
        print(f"Database already contains {count} records. Skipping population.")
    
    app.run(host='0.0.0.0', port=5020, debug=True)
