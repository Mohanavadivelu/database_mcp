"""
Database connection management for the Database MCP project.

This module handles SQLite database connections and basic operations.
"""

import sqlite3
import os
from pathlib import Path

# Get the database path relative to this file
DB_PATH = Path(__file__).parent / 'usage.db'

def get_db_connection():
    """
    Creates and returns a SQLite database connection.
    
    Returns:
        sqlite3.Connection: Database connection object with row factory enabled.
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def init_database():
    """
    Initialize the database with required tables if they don't exist.
    """
    conn = get_db_connection()
    try:
        # Create usage_data table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usage_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                application_name TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
    finally:
        conn.close()

def get_table_count(table_name='usage_data'):
    """
    Get the number of records in a table.
    
    Args:
        table_name (str): Name of the table to count records from.
        
    Returns:
        int: Number of records in the table.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        print(f"❌ Error counting records: {e}")
        return 0
    finally:
        conn.close()
