# prompts.py
"""
Contains prompt templates used by the application
"""

SQL_FEW_SHOT_EXAMPLES = [
    {
        "question": "What is the total usage duration of Photoshop?",
        "sql": "SELECT SUM(duration_seconds) AS result FROM usage_data WHERE LOWER(application_name) = 'photoshop';"
    },
    {
        "question": "How many distinct users are using Windows?",
        "sql": "SELECT COUNT(DISTINCT user) AS result FROM usage_data WHERE LOWER(platform) = 'windows';"
    },
    {
        "question": "Which user used Slack the most in the last 7 days?",
        "sql": """
        SELECT user, SUM(duration_seconds) AS result
        FROM usage_data
        WHERE LOWER(application_name) = 'slack'
          AND log_date BETWEEN strftime('%Y-%m-%dT%H:%M:%SZ', datetime('now', '-7 days'))
                          AND strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
        GROUP BY user
        ORDER BY result DESC
        LIMIT 1;
        """.strip()
    },
    {
        "question": "List all distinct legacy applications being tracked.",
        "sql": "SELECT DISTINCT application_name FROM usage_data WHERE legacy_app = 1;"
    },
    {
        "question": "What is the average session duration for VS Code?",
        "sql": "SELECT AVG(duration_seconds) AS result FROM usage_data WHERE LOWER(application_name) = 'vscode';"
    },
    {
        "question": "Which are the top 3 most used applications by total duration?",
        "sql": """
        SELECT application_name, SUM(duration_seconds) AS result
        FROM usage_data
        GROUP BY application_name
        ORDER BY result DESC
        LIMIT 3;
        """.strip()
    },
    {
        "question": "Which user has the longest total usage time on macOS?",
        "sql": """
        SELECT user, SUM(duration_seconds) AS result
        FROM usage_data
        WHERE LOWER(platform) = 'macos'
        GROUP BY user
        ORDER BY result DESC
        LIMIT 1;
        """.strip()
    },
    {
        "question": "How many legacy applications are used on Windows?",
        "sql": """
        SELECT COUNT(DISTINCT application_name) AS result
        FROM usage_data
        WHERE legacy_app = 1 AND LOWER(platform) = 'windows';
        """.strip()
    },
    {
        "question": "Which user spent the most time using apps last month?",
        "sql": """
        SELECT user, SUM(duration_seconds) AS result
        FROM usage_data
        WHERE log_date BETWEEN strftime('%Y-%m-01T00:00:00Z', 'now', '-1 month')
                          AND strftime('%Y-%m-%dT23:59:59Z', 'now', 'start of month', '-1 day')
        GROUP BY user
        ORDER BY result DESC
        LIMIT 1;
        """.strip()
    },
    {
        "question": "Break down usage time per user per application.",
        "sql": """
        SELECT user, application_name, SUM(duration_seconds) AS result
        FROM usage_data
        GROUP BY user, application_name
        ORDER BY user, result DESC;
        """.strip()
    }
]


def get_sql_generation_prompt(schema):
    """Returns an optimized prompt for generating SQLite queries from natural language using the given schema."""
    examples_str = "\n\n".join([
        f"Question: {ex['question']}\nSQL: {ex['sql']}"
        for ex in SQL_FEW_SHOT_EXAMPLES
    ])

    return f"""
        You are an expert SQLite assistant. Your task is to convert a user's natural language question into a single, valid SQLite query based on the following database schema.

        - Table
        - `usage_data`

        - Schema
        - `id` (INTEGER, PRIMARY KEY AUTOINCREMENT): Unique identifier for each usage record.
        - `monitor_app_version` (TEXT NOT NULL): Version of the monitoring tool that logged the data.
        - `platform` (TEXT NOT NULL): Operating system (e.g., Windows, macOS, Android).
        - `user` (TEXT NOT NULL): Username or device ID.
        - `application_name` (TEXT NOT NULL): Name of the application (e.g., chrome.exe).
        - `application_version` (TEXT NOT NULL): Application version number.
        - `log_date` (TEXT NOT NULL): ISO 8601 timestamp (`YYYY-MM-DDTHH:MM:SSZ`).
        - `legacy_app` (BOOLEAN NOT NULL): Indicates if the application is legacy (true/false).
        - `duration_seconds` (INTEGER NOT NULL): Usage time in seconds.

        - Query Guidelines
        - Use `SELECT DISTINCT user` for listing unique users.
        - Use `COUNT(*)` for "most used" or "most frequent".
        - Use `SUM(duration_seconds)` for "longest used".
        - Always alias aggregates as `result`.
        - Use `LOWER()` for case-insensitive text comparisons.
        - Use `ORDER BY` with `LIMIT` for top/bottom N queries.

        - Date Filters (used with `log_date`)
        - Today:
            `strftime('%Y-%m-%dT%H:%M:%SZ', 'now', 'localtime')`
        - Yesterday:
            `strftime('%Y-%m-%dT%H:%M:%SZ', 'now', 'localtime', '-1 day')`
        - Last 7 days:
            `log_date BETWEEN strftime('%Y-%m-%dT%H:%M:%SZ', datetime('now', '-7 days')) AND strftime('%Y-%m-%dT%H:%M:%SZ', 'now')`
        - Last month:
            `log_date BETWEEN strftime('%Y-%m-01T00:00:00Z', 'now', '-1 month') AND strftime('%Y-%m-%dT23:59:59Z', 'now', 'start of month', '-1 day')`

        - Output Policy
        - Only return the raw SQL query. Do not include explanations or comments.

        - Examples
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
