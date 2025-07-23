# core/app.py
# Flask web interface for the database querying system
# This file provides a web interface while the MCP server (mcp_server.py) provides protocol access

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import sqlite3
import json
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

# Import our shared database query engine
from database.query_engine import DatabaseQueryEngine
from database.models import DATABASE
from database.connection import get_db_connection

# --- 1. CONFIGURATION ---
# Load environment variables from .env file if present
load_dotenv()

# --- 2. FLASK APPLICATION SETUP ---
app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

# Initialize database query engine for web interface
try:
    db_engine = DatabaseQueryEngine()
    print("✅ Flask app initialized with database query engine")
except Exception as e:
    print(f"❌ Failed to initialize database engine: {e}")
    db_engine = None

# --- 3. HELPER FUNCTIONS ---
def get_db_connection_legacy():
    """Legacy helper function for backward compatibility."""
    return get_db_connection()

# --- 4. API ENDPOINTS ---
@app.route('/api/llm_query', methods=['POST'])
def llm_query():
    """Handle LLM-powered database queries via API."""
    if not db_engine:
        return jsonify({
            'success': False, 
            'error': 'Database engine not initialized'
        }), 500
    
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return jsonify({
                'success': False, 
                'error': 'Query is required'
            }), 400
        
        # Use the shared database query engine
        result = db_engine.process_natural_language_query(user_query)
        
        # Add success flag for compatibility
        result['success'] = True
        
        # Store successful queries in history
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO query_history (query, sql_query, response, success)
                VALUES (?, ?, ?, ?)
            ''', (
                user_query,
                result.get('sql', ''),  # Changed from 'sql_query' to 'sql'
                json.dumps(result),
                1
            ))
            conn.commit()
        except Exception as e:
            print(f"Warning: Failed to save query to history: {e}")
        finally:
            conn.close()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in llm_query: {e}")
        return jsonify({
            'success': False, 
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/history', methods=['GET'])
def get_query_history():
    """Get query history from database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, query, sql_query, response, success, timestamp
            FROM query_history 
            ORDER BY timestamp DESC 
            LIMIT 50
        ''')
        
        history = []
        for row in cursor.fetchall():
            try:
                response_data = json.loads(row['response']) if row['response'] else {}
            except json.JSONDecodeError:
                response_data = {'error': 'Invalid JSON in stored response'}
            
            history.append({
                'id': row['id'],
                'query': row['query'],
                'sql_query': row['sql_query'],
                'response': response_data,
                'success': bool(row['success']),
                'timestamp': row['timestamp']
            })
        
        conn.close()
        return jsonify({'success': True, 'history': history})
        
    except Exception as e:
        print(f"Error getting history: {e}")
        return jsonify({
            'success': False, 
            'error': f'Failed to retrieve history: {str(e)}'
        }), 500

@app.route('/api/history/<int:history_id>', methods=['DELETE'])
def delete_history_item(history_id):
    """Delete a specific history item."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM query_history WHERE id = ?', (history_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({
                'success': False, 
                'error': 'History item not found'
            }), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error deleting history item: {e}")
        return jsonify({
            'success': False, 
            'error': f'Failed to delete history item: {str(e)}'
        }), 500

# --- 5. WEB ROUTES ---
@app.route('/')
def index():
    """Serve the main interface."""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
