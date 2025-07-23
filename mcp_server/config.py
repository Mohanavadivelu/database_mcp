"""
MCP Server configuration and settings.

This module handles configuration for the MCP server component.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class MCPServerConfig:
    """Configuration for MCP Server."""
    
    # Server identification
    SERVER_NAME = "database-mcp"
    SERVER_VERSION = "1.0.0"
    
    # Database settings
    DATABASE_PATH = Path(__file__).parent.parent / 'database' / 'usage.db'
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    # MCP Protocol settings
    PROTOCOL_VERSION = "2024-11-05"
    
    # Tool definitions
    AVAILABLE_TOOLS = [
        "query_database",
        "get_schema",
        "get_statistics"
    ]
