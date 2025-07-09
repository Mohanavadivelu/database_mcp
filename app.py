# app.py
#
# This file contains the complete Flask server for the MCP (Monitoring and Control Panel).
# It features a natural language interface powered by a two-step LLM process (OpenAI's GPT)
# to query a SQLite database and provide human-readable answers.

import os
import sqlite3
import json
import openai
from flask import Flask, jsonify, render_template, request

# --- 1. CONFIGURATION ---

# Database configuration
DATABASE = 'usage.db'

# The database schema. This is critical context for the LLM to generate correct SQL.
DATABASE_SCHEMA = """
CREATE TABLE usage_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_app_version TEXT NOT NULL,
    platform TEXT NOT NULL,
    user TEXT NOT NULL,
    application_name TEXT NOT NULL,
    application_version TEXT NOT NULL,
    log_date TEXT NOT NULL, -- Stored as ISO 8601 format text (e.g., '2023-10-27T10:00:00Z')
    legacy_app BOOLEAN NOT NULL, -- 1 for True, 0 for False
    duration_seconds INTEGER NOT NULL
)
"""

# OpenAI API client initialization.
# It automatically looks for the OPENAI_API_KEY environment variable.
try:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        print("!!! WARNING: OPENAI_API_KEY environment variable not set. LLM features will fail.")
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")


# --- 2. FLASK APPLICATION SETUP ---

app = Flask(__name__)


# --- 3. HELPER FUNCTIONS ---

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    # Allows accessing columns by name (like a dictionary).
    conn.row_factory = sqlite3.Row
    return conn


# --- 4. API ENDPOINTS ---

@app.route('/api/llm_query', methods=['POST'])
def handle_llm_query():
    """
    Handles a natural language query using a two-step LLM process:
    1. Text-to-SQL: Convert the user's question into an SQL query.
    2. Data-to-Text: Interpret the SQL result to formulate a human-readable answer.
    """
    user_question = request.json.get('question')
    if not user_question:
        return jsonify({'error': 'No question provided'}), 400
    
    if not openai.api_key:
        return jsonify({'answer': "Server Error: OpenAI API key is not configured."}), 500

    try:
        # === STEP 1: TEXT-TO-SQL -- Generate the SQL Query ===
        sql_generation_prompt = f"""
        You are an expert SQLite assistant. Your task is to convert a user's natural language question into a single, valid SQLite query based on the following database schema.
        - The database table is named `usage_data`.
        - The schema is: {DATABASE_SCHEMA}
        - When asked for the 'most used' or 'most frequent' app, use COUNT. When asked for 'longest used', use SUM of duration_seconds.
        - CRITICAL RULE: When calculating (SUM, COUNT, etc.), always alias the result column as `result`.
        - Compare strings case-insensitively using `lower()`.
        - Only respond with the raw SQL query and nothing else.
        """
        
        client = openai.OpenAI()
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": sql_generation_prompt},
                {"role": "user", "content": user_question}
            ],
            temperature=0.0 # Low temperature for precise, deterministic SQL
        )
        # Clean up the response from the LLM
        generated_sql = completion.choices[0].message.content.strip().replace('`', '')

        # A minimal security check to prevent destructive or complex queries.
        if not generated_sql.upper().startswith("SELECT"):
            raise ValueError("LLM generated a non-SELECT query. Aborting for safety.")

        # === STEP 2: EXECUTE SQL -- Get the data from the database ===
        conn = get_db_connection()
        results = conn.execute(generated_sql).fetchall()
        conn.close()

        if not results:
            return jsonify({'answer': "I couldn't find any data that answers your question."})

        # Convert the database result into a simple JSON string for the next prompt.
        data_from_db = json.dumps([dict(row) for row in results])

        # === STEP 3: DATA-TO-TEXT -- Interpret the result and create a natural language answer ===
        interpretation_prompt = f"""
        You are a helpful data analyst assistant. Your job is to provide a concise, natural language answer to a user's question based on the data provided.
        Do not just repeat the data; interpret it in a friendly and direct way. If the data is a list of items, summarize it if appropriate.
        ---
        User's Original Question: "{user_question}"
        ---
        Data Result from Database (in JSON format):
        {data_from_db}
        ---
        Your concise, natural language answer:
        """

        final_completion = client.chat.completions.create(
            model="gpt-3.5-turbo-0125", # Use a good, modern model for conversational responses
            messages=[
                {"role": "system", "content": "You are a helpful data analyst assistant who provides clear, natural language answers based on data."},
                {"role": "user", "content": interpretation_prompt}
            ],
            temperature=0.5 # A little creativity is good for conversational answers
        )
        
        final_answer = final_completion.choices[0].message.content.strip()

        return jsonify({'answer': final_answer})

    except openai.APIError as e:
        return jsonify({'answer': f"An error occurred with the OpenAI API: {e}"}), 500
    except Exception as e:
        # Catches SQL errors, the security check error, or other issues.
        return jsonify({'answer': f"An error occurred: {e}"}), 500


# --- 5. FRONTEND ROUTE ---

@app.route('/')
def index():
    """Serves the main frontend page (templates/index.html)."""
    return render_template('index.html')


# --- 6. MAIN EXECUTION BLOCK ---

if __name__ == '__main__':
    # This block runs when the script is executed directly.
    
    # It's important to have the 'database.py' script in the same directory.
    # This ensures the database and table are created before starting the server.
    import database
    database.init_db()
    
    # Adds sample data for testing purposes on each startup (in debug mode).
    database.add_sample_data()
    
    # Run the Flask application.
    # host='0.0.0.0' makes the server accessible on your local network.
    # debug=True enables auto-reloading when code changes, which is great for development.
    app.run(host='0.0.0.0', port=5000, debug=True)