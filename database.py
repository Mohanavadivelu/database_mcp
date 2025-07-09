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

def add_sample_data():
    """Adds some sample data to the database for testing."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Check if data already exists to prevent duplicates
    cursor.execute("SELECT COUNT(*) from usage_data")
    if cursor.fetchone()[0] > 0:
        print("Sample data already exists.")
        conn.close()
        return

    print("Adding sample data...")
    sample_data = [
        ('1.2.0', 'Windows', 'alice', 'Photoshop', '22.1', '2023-10-26T10:00:00Z', False, 1250),
        ('1.2.0', 'macOS', 'bob', 'VSCode', '1.70.1', '2023-10-26T10:05:00Z', False, 3600),
        ('1.1.5', 'Windows', 'alice', 'OldApp', '2.5', '2023-10-26T11:00:00Z', True, 720)
    ]
    cursor.executemany("""
        INSERT INTO usage_data (
            monitor_app_version, platform, user, application_name, application_version,
            log_date, legacy_app, duration_seconds
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_data)
    print("Sample data added.")

    conn.commit()
    conn.close()


# This allows you to run `python database.py` from the terminal to set things up
if __name__ == '__main__':
    init_db()
    add_sample_data()