# database.py
import sqlite3

DATABASE_NAME = 'usage.db'

def init_db():
    """Initializes the database and creates the table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    print("Creating 'usage_data' table...")
    # The CREATE TABLE statement you provided
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monitor_app_version TEXT NOT NULL,
            platform TEXT NOT NULL,
            user TEXT NOT NULL,
            application_name TEXT NOT NULL,
            application_version TEXT NOT NULL,
            log_date TEXT NOT NULL,
            legacy_app BOOLEAN NOT NULL,
            duration_seconds INTEGER NOT NULL
        )
    """)
    print("Table created successfully.")

    conn.commit()
    conn.close()

# This allows you to run `python database.py` from the terminal to set things up
if __name__ == '__main__':
    init_db()
