# prompts.py
"""
Contains prompt templates used by the application
"""

def get_sql_generation_prompt(schema):
    """Returns the prompt for SQL generation with the given schema"""
    return f"""
    You are an expert SQLite assistant. Your task is to convert a user's natural language question into a single, valid SQLite query based on the following database schema.
    - The database table is named `usage_data`.
    - The schema is: {schema}
    - IMPORTANT: If the user asks to "list all users", they want a unique list of names, so use "SELECT DISTINCT user FROM usage_data".
    - When asked for the 'most used' or 'most frequent' app, use COUNT. When asked for 'longest used', use SUM of duration_seconds.
    - CRITICAL RULE: When calculating (SUM, COUNT, etc.), always alias the result column as `result`.
    - Compare strings case-insensitively using `lower()`.
    - Only respond with the raw SQL query and nothing else.
    """

def get_data_interpretation_prompt(user_question, data_json):
    """Returns the prompt for data interpretation"""
    return f"""
    You are a helpful data analyst assistant. Your job is to provide a concise, natural language answer to a user's question based on the data provided.
    Do not just repeat the data; interpret it in a friendly and direct way. If the data is a list, summarize it if appropriate.
    ---
    User's Original Question: "{user_question}"
    ---
    Data Result from Database (in JSON format):
    {data_json}
    ---
    Your concise, natural language answer:
    """
