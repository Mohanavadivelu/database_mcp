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
def llm_query():
    """
    Main API endpoint that converts natural language questions into SQL queries,
    executes them, and returns human-readable answers using LLM processing.
    
    This function implements a 4-step pipeline:
    1. Input validation and security checks
    2. Text-to-SQL conversion using LLM
    3. SQL execution and result processing
    4. Data-to-text conversion for human-readable response
    """
    
    # Step 0: Initialize constants and extract request parameters
    # Token limit considerations:
    # - GPT-3.5-turbo: 4,096 tokens (conservative: 200 rows)
    # - GPT-3.5-turbo-0125: 16,385 tokens (optimal: 500 rows)
    # - Each row ≈ 50-100 tokens, system prompt ≈ 300 tokens, response buffer ≈ 1000 tokens
    MAX_ROWS_FOR_LLM_SUMMARY = 200  # Balanced limit for good performance and comprehensive analysis
    
    # Extract pagination parameters (for future use)
    data = request.get_json()
    question = data.get('question', '')
    page = int(data.get('page', 1))
    page_size = int(data.get('page_size', 20))

    # Step 1: INPUT VALIDATION AND SECURITY CHECKS
    print("🔍 Step 1: Validating input and performing security checks...")
    
    # 1.1: Ensure request is valid JSON
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    # 1.2: Extract and validate the user question
    user_question = request.json.get('question', '').strip()
    if not user_question:
        return jsonify({'error': 'No question provided'}), 400
    
    # 1.3: Security check - prevent SQL injection and harmful operations
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE']
    if any(keyword in user_question.upper() for keyword in dangerous_keywords):
        return jsonify({'error': 'Potentially harmful question detected'}), 400
    
    # 1.4: Verify OpenAI API key is configured
    if not openai.api_key:
        return jsonify({'answer': "Server Error: OpenAI API key is not configured."}), 500

    try:
        # Step 2: PREPARE FOR TEXT-TO-SQL CONVERSION
        print("📋 Step 2: Preparing database schema and LLM prompts...")
        
        # 2.1: Import prompt generation functions
        from prompts import get_sql_generation_prompt, get_data_interpretation_prompt
        
        # 2.2: Retrieve database schema for the usage_data table
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='usage_data'")
        schema_result = cursor.fetchone()
        if not schema_result:
            return jsonify({'error': 'Database schema not found for usage_data table.'}), 500
        
        DATABASE_SCHEMA = schema_result[0]  # This contains the CREATE TABLE statement
        conn.close()

        # 2.3: Generate the SQL generation prompt with schema context
        sql_generation_prompt = get_sql_generation_prompt(DATABASE_SCHEMA)
        
        # Step 3: TEXT-TO-SQL CONVERSION USING LLM
        print("🤖 Step 3: Converting natural language to SQL using LLM...")
        
        # 3.1: Initialize OpenAI client and make API call
        client = openai.OpenAI()
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": sql_generation_prompt},
                {"role": "user", "content": user_question}
            ],
            temperature=0.0  # Use deterministic output for SQL generation
        )
        
        # 3.2: Extract and clean the generated SQL
        generated_sql = completion.choices[0].message.content.strip().replace('`', '')
        print(f"Generated SQL: {generated_sql}")

        # 3.3: Security validation - ensure only SELECT queries are executed
        if not generated_sql.upper().startswith("SELECT"):
            raise ValueError("LLM generated a non-SELECT query. Aborting for safety.")

        # 3.4: Add pagination to SQL if not already present (for future pagination feature)
        if generated_sql.strip().lower().startswith("select") and "limit" not in generated_sql.lower():
            offset = (page - 1) * page_size
            generated_sql = generated_sql.rstrip(";") + f" LIMIT {page_size} OFFSET {offset};"

        # Step 4: SQL EXECUTION AND RESULT PROCESSING
        print("💾 Step 4: Executing SQL query and processing results...")
        
        # 4.1: Execute the generated SQL query
        conn = get_db_connection()
        results = conn.execute(generated_sql).fetchall()
        conn.close()
        
        print(f"Query returned {len(results)} rows")

        # 4.2: Handle empty results
        if not results:
            return jsonify({'answer': "I couldn't find any data that answers your question."})
        
        # Step 5: CIRCUIT BREAKER - HANDLE LARGE RESULT SETS
        print("🔄 Step 5: Checking result set size...")
        
        # 5.1: If results are too large, return sample data instead of LLM processing
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

        # Step 6: DATA-TO-TEXT CONVERSION USING LLM
        print("📝 Step 6: Converting data to human-readable response...")
        
        # 6.1: Prepare data for LLM interpretation
        data_from_db = json.dumps([dict(row) for row in results])
        interpretation_prompt = get_data_interpretation_prompt(user_question, data_from_db)

        # 6.2: Generate human-readable interpretation of the data
        final_completion = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": "You are a helpful data analyst assistant who provides clear, natural language answers based on data."},
                {"role": "user", "content": interpretation_prompt}
            ],
            temperature=0.5  # Allow some creativity in response formatting
        )
        
        # 6.3: Extract final answer and prepare response
        final_answer = final_completion.choices[0].message.content.strip()
        
        # Step 7: RETURN SUCCESSFUL RESPONSE
        print("✅ Step 7: Returning successful response to client...")
        return jsonify({
            'answer': final_answer,           # Human-readable response
            'data': [dict(row) for row in results],  # Raw data for charts/export
            'question': user_question         # Echo back the original question
        })

    # Step 8: ERROR HANDLING
    except openai.APIError as e:
        print("❌ OpenAI API Error occurred")
        error_message = f"An error occurred with the OpenAI API: {e}"
        print(error_message)
        return jsonify({'answer': error_message}), 500
    except Exception as e:
        print("❌ General error occurred")
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
