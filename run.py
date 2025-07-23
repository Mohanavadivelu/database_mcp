#!/usr/bin/env python3
"""
Main application entry point for the Database MCP project.

This script serves as the primary entry point to run the Flask web application.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.app import app
from database.connection import init_database

def main():
    """Main application entry point."""
    print("🚀 Starting Database MCP Application...")
    
    # Initialize database
    init_database()
    
    # Start Flask application
    if __name__ == "__main__":
        # Development mode
        app.run(
            host='0.0.0.0',
            port=5020,
            debug=True
        )

if __name__ == "__main__":
    main()
