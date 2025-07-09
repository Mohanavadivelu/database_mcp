# app.py

import os
import sqlite3
import json
import openai
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

# --- 1. CONFIGURATION ---
# Load environment variables from .env file if present
load_dotenv()

DATABASE = 'usage.db'

# More robust API key handling
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("!!! WARNING: OPENAI_API_KEY environment variable not set. LLM features will fail.")
    print("Create a .env file with OPENAI_API_KEY=your_key or set it in your environment.")
else:
    try:
        openai.api_key = OPENAI_API_KEY
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")

# --- 2. FLASK APPLICATION SETUP ---
app = Flask(__name__)

# --- 3. HELPER FUNCTIONS ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# --- 4. API ENDPOINTS ---
@app.route('/api/llm_query', methods=['POST'])
def handle_llm_query():
    MAX_ROWS_FOR_LLM_SUMMARY = 50
    
    # Input validation
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    user_question = request.json.get('question', '').strip()
    if not user_question:
        return jsonify({'error': 'No question provided'}), 400
    
    # Check for potentially harmful inputs
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE']
    if any(keyword in user_question.upper() for keyword in dangerous_keywords):
        return jsonify({'error': 'Potentially harmful question detected'}), 400
    
    if not openai.api_key:
        return jsonify({'answer': "Server Error: OpenAI API key is not configured."}), 500

    try:
        # Import prompts
        from prompts import get_sql_generation_prompt, get_data_interpretation_prompt
        
        # === STEP 1: TEXT-TO-SQL ===
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='usage_data'")
        schema_result = cursor.fetchone()
        if not schema_result:
            return jsonify({'error': 'Database schema not found for usage_data table.'}), 500
        
        DATABASE_SCHEMA = schema_result[0]
        conn.close()

        sql_generation_prompt = get_sql_generation_prompt(DATABASE_SCHEMA)
        
        client = openai.OpenAI()
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": sql_generation_prompt},
                {"role": "user", "content": user_question}
            ],
            temperature=0.0
        )
        generated_sql = completion.choices[0].message.content.strip().replace('`', '')

        # Security check
        if not generated_sql.upper().startswith("SELECT"):
            raise ValueError("LLM generated a non-SELECT query. Aborting for safety.")

        # === STEP 2: EXECUTE SQL ===
        conn = get_db_connection()
        results = conn.execute(generated_sql).fetchall()
        conn.close()

        if not results:
            return jsonify({'answer': "I couldn't find any data that answers your question."})
        
        # === STEP 3: CIRCUIT BREAKER ===
        if len(results) > MAX_ROWS_FOR_LLM_SUMMARY:
            total_rows = len(results)
            sample_data = [dict(row) for row in results[:10]]
            human_answer = (
                f"Your query returned {total_rows} rows, which is too large to summarize.\n"
                f"Please try a more specific question (e.g., 'who were the top 5 most active users last week?').\n\n"
                f"Here is a sample of the first 10 rows:\n"
                f"{json.dumps(sample_data, indent=2)}"
            )
            return jsonify({'answer': human_answer})

        # === STEP 4: DATA-TO-TEXT ===
        data_from_db = json.dumps([dict(row) for row in results])
        interpretation_prompt = get_data_interpretation_prompt(user_question, data_from_db)

        final_completion = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": "You are a helpful data analyst assistant who provides clear, natural language answers based on data."},
                {"role": "user", "content": interpretation_prompt}
            ],
            temperature=0.5
        )
        
        final_answer = final_completion.choices[0].message.content.strip()
        return jsonify({'answer': final_answer})

    except openai.APIError as e:
        error_message = f"An error occurred with the OpenAI API: {e}"
        print(error_message)
        return jsonify({'answer': error_message}), 500
    except Exception as e:
        error_message = f"An internal server error occurred: {e}"
        print(error_message)
        return jsonify({'answer': error_message}), 500

# --- 5. FRONTEND ROUTE ---
@app.route('/')
def index():
    return render_template('index.html')

# --- 6. MAIN EXECUTION BLOCK ---
if __name__ == '__main__':
    import database
    import populate_database

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
    
    app.run(host='0.0.0.0', port=5000, debug=True)
