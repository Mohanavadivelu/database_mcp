# prompts.py
"""
Contains prompt templates used by the application
"""

SQL_FEW_SHOT_EXAMPLES = [
    {
        "question": "show me total duration for photoshop",
        "sql": "SELECT SUM(duration_seconds) AS result FROM usage_data WHERE lower(application_name) = 'photoshop';"
    },
    {
        "question": "how many unique users on windows?",
        "sql": "SELECT COUNT(DISTINCT user) AS result FROM usage_data WHERE lower(platform) = 'windows';"
    },
    {
        "question": "who used the most slack last week?",
        "sql": "SELECT user, SUM(duration_seconds) AS result FROM usage_data WHERE lower(application_name) = 'slack' AND log_date BETWEEN strftime('%Y-%m-%dT%H:%M:%SZ', datetime('now', '-7 days')) AND strftime('%Y-%m-%dT%H:%M:%SZ', 'now') GROUP BY user ORDER BY result DESC LIMIT 1;"
    },
    {
        "question": "list all legacy apps",
        "sql": "SELECT DISTINCT application_name FROM usage_data WHERE legacy_app = 1;"
    },
    {
        "question": "what was the average duration of vscode sessions?",
        "sql": "SELECT AVG(duration_seconds) AS result FROM usage_data WHERE lower(application_name) = 'vscode';"
    }
]

def get_sql_generation_prompt(schema):
    """Returns the prompt for SQL generation with the given schema"""
    examples_str = "\n".join([f"Question: {ex['question']}\nSQL: {ex['sql']}" for ex in SQL_FEW_SHOT_EXAMPLES])

    return f"""
    You are an expert SQLite assistant. Your task is to convert a user's natural language question into a single, valid SQLite query based on the following database schema.
    - The database table is named `usage_data`.
    - The schema is: {schema}
    - IMPORTANT:
        - When asked for a list of distinct users, use `SELECT DISTINCT user FROM usage_data`.
        - When asked for "most used" or "most frequent", use `COUNT`.
        - When asked for "longest used", use `SUM(duration_seconds)`.
        - When calculating aggregates (SUM, COUNT, AVG), always alias the result column as `result`.
        - Compare strings case-insensitively using `lower()`.
        - Dates are stored in ISO 8601 format (e.g., 'YYYY-MM-DDTHH:MM:SSZ'). Use SQLite's `strftime` and `datetime` functions for date comparisons and calculations. Examples:
            - 'today': `strftime('%Y-%m-%dT%H:%M:%SZ', 'now', 'localtime')`
            - 'yesterday': `strftime('%Y-%m-%dT%H:%M:%SZ', 'now', 'localtime', '-1 day')`
            - 'last 7 days': `log_date BETWEEN strftime('%Y-%m-%dT%H:%M:%SZ', datetime('now', '-7 days')) AND strftime('%Y-%m-%dT%H:%M:%SZ', 'now')`
            - 'last month': `log_date BETWEEN strftime('%Y-%m-01T00:00:00Z', 'now', '-1 month') AND strftime('%Y-%m-%dT23:59:59Z', 'now', 'start of month', '-1 day')`
        - For "top N" or "bottom N" type queries, use `ORDER BY` and `LIMIT`.

    Only respond with the raw SQL query and nothing else.

    Here are some examples to guide you:
    {examples_str}
    """

def get_data_interpretation_prompt(user_question, data_json):
    """Returns the prompt for data interpretation"""
    return f"""
    You are a helpful data analyst assistant. Your job is to provide a concise, natural language answer and insightful interpretation to a user's original question based on the provided data.
    
    Do not just repeat the data. Instead:
    - **Interpret:** Explain what the data means in simple terms.
    - **Summarize:** If the data is a list, summarize it effectively.
    - **Identify Patterns:** Look for trends, outliers, or anything noteworthy in the dataset.

    ---
    User's Original Question: "{user_question}"
    ---
    Data Result from Database (in JSON format):
    {data_json}
    ---
    Your concise, natural language answer and interpretation:
    """
