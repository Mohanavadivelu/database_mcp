# mcp_server.py
# Model Context Protocol (MCP) server implementation for database querying

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional, Sequence

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    ListResourcesResult,
    Resource,
    ReadResourceResult,
)

# Import our database query engine
from database_tools import DatabaseQueryEngine, process_database_query

# Server information
SERVER_NAME = "database-mcp"
SERVER_VERSION = "1.0.0"

# Initialize the MCP server
server = Server(SERVER_NAME)

# Initialize database query engine
try:
    db_engine = DatabaseQueryEngine()
    print(f"✅ {SERVER_NAME} v{SERVER_VERSION} initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize database engine: {e}")
    sys.exit(1)

@server.list_tools()
async def list_tools() -> ListToolsResult:
    """
    List available tools that can be called by MCP clients.
    
    Returns:
        ListToolsResult containing available tools
    """
    return ListToolsResult(
        tools=[
            Tool(
                name="query_database",
                description=(
                    "Query a usage tracking database using natural language. "
                    "This tool converts natural language questions into SQL queries, "
                    "executes them against a SQLite database containing user activity data, "
                    "and returns human-readable answers along with the raw data."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": (
                                "Natural language question about the usage data. "
                                "Examples: 'How many hours did alice spend on photoshop?', "
                                "'What were the most used applications last week?', "
                                "'Show me all users on Windows platform'"
                            )
                        }
                    },
                    "required": ["question"]
                }
            ),
            Tool(
                name="get_database_schema",
                description=(
                    "Get the database schema information to understand "
                    "what data is available for querying."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            ),
            Tool(
                name="execute_sql",
                description=(
                    "Execute a raw SQL SELECT query against the database. "
                    "Use this for advanced users who want to write their own SQL queries. "
                    "Only SELECT statements are allowed for security."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": (
                                "SQL SELECT query to execute. Must start with SELECT. "
                                "Example: 'SELECT user, SUM(duration_seconds) FROM usage_data GROUP BY user'"
                            )
                        }
                    },
                    "required": ["sql"]
                }
            )
        ]
    )

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle tool calls from MCP clients.
    
    Args:
        name: Name of the tool to call
        arguments: Dictionary of arguments for the tool
        
    Returns:
        CallToolResult containing the tool execution results
    """
    try:
        if name == "query_database":
            return await handle_database_query(arguments)
        elif name == "get_database_schema":
            return await handle_get_schema(arguments)
        elif name == "execute_sql":
            return await handle_execute_sql(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        # Return error as text content
        error_msg = f"Error executing tool '{name}': {str(e)}"
        print(f"❌ {error_msg}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=error_msg
                )
            ],
            isError=True
        )

async def handle_database_query(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle natural language database queries.
    
    Args:
        arguments: Dictionary containing 'question' key
        
    Returns:
        CallToolResult with query results
    """
    question = arguments.get("question", "").strip()
    if not question:
        raise ValueError("Question parameter is required")
    
    print(f"🔍 Processing natural language query: {question}")
    
    # Process the query using our database engine
    result = db_engine.process_natural_language_query(question)
    
    # Format response for MCP client
    response_text = f"**Question:** {result['question']}\n\n"
    response_text += f"**Answer:** {result['answer']}\n\n"
    
    if result['data']:
        response_text += f"**Data Summary:**\n"
        response_text += f"- Returned {len(result['data'])} rows\n"
        response_text += f"- Generated SQL: `{result['sql']}`\n\n"
        
        # Include sample of data if available
        if len(result['data']) <= 10:
            response_text += "**Raw Data:**\n"
            response_text += f"```json\n{json.dumps(result['data'], indent=2)}\n```"
        else:
            response_text += "**Sample Data (first 5 rows):**\n"
            response_text += f"```json\n{json.dumps(result['data'][:5], indent=2)}\n```"
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=response_text
            )
        ]
    )

async def handle_get_schema(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle database schema requests.
    
    Args:
        arguments: Empty dictionary (no arguments required)
        
    Returns:
        CallToolResult with schema information
    """
    print("📋 Retrieving database schema...")
    
    try:
        schema = db_engine.get_database_schema()
        
        # Also get some sample data to show what's available
        conn = db_engine.get_db_connection()
        sample_query = "SELECT * FROM usage_data LIMIT 3"
        sample_results = conn.execute(sample_query).fetchall()
        sample_data = [dict(row) for row in sample_results]
        conn.close()
        
        response_text = "**Database Schema:**\n\n"
        response_text += f"```sql\n{schema}\n```\n\n"
        response_text += "**Sample Data:**\n"
        response_text += f"```json\n{json.dumps(sample_data, indent=2)}\n```\n\n"
        response_text += "**Available Fields:**\n"
        
        if sample_data:
            for field in sample_data[0].keys():
                response_text += f"- `{field}`\n"
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=response_text
                )
            ]
        )
        
    except Exception as e:
        raise ValueError(f"Failed to retrieve schema: {str(e)}")

async def handle_execute_sql(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle raw SQL execution requests.
    
    Args:
        arguments: Dictionary containing 'sql' key
        
    Returns:
        CallToolResult with query results
    """
    sql = arguments.get("sql", "").strip()
    if not sql:
        raise ValueError("SQL parameter is required")
    
    # Security check - only allow SELECT statements
    if not sql.upper().startswith("SELECT"):
        raise ValueError("Only SELECT statements are allowed for security reasons")
    
    print(f"💾 Executing raw SQL: {sql}")
    
    try:
        results = db_engine.execute_sql_query(sql)
        data = [dict(row) for row in results]
        
        response_text = f"**Executed SQL:** `{sql}`\n\n"
        response_text += f"**Results:** {len(data)} rows returned\n\n"
        
        if data:
            if len(data) <= 20:
                response_text += "**Data:**\n"
                response_text += f"```json\n{json.dumps(data, indent=2)}\n```"
            else:
                response_text += "**Sample Data (first 10 rows):**\n"
                response_text += f"```json\n{json.dumps(data[:10], indent=2)}\n```"
                response_text += f"\n*Note: Showing 10 of {len(data)} total rows*"
        else:
            response_text += "No data returned."
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=response_text
                )
            ]
        )
        
    except Exception as e:
        raise ValueError(f"SQL execution failed: {str(e)}")

@server.list_resources()
async def list_resources() -> ListResourcesResult:
    """
    List available resources that can be read by MCP clients.
    
    Returns:
        ListResourcesResult containing available resources
    """
    return ListResourcesResult(
        resources=[
            Resource(
                uri="database://usage_data/schema",
                name="Database Schema",
                description="SQLite schema for the usage_data table",
                mimeType="application/sql"
            ),
            Resource(
                uri="database://usage_data/sample",
                name="Sample Data",
                description="Sample records from the usage_data table",
                mimeType="application/json"
            )
        ]
    )

@server.read_resource()
async def read_resource(uri: str) -> ReadResourceResult:
    """
    Read a specific resource by URI.
    
    Args:
        uri: Resource URI to read
        
    Returns:
        ReadResourceResult containing the resource content
    """
    if uri == "database://usage_data/schema":
        schema = db_engine.get_database_schema()
        return ReadResourceResult(
            contents=[
                TextContent(
                    type="text",
                    text=schema
                )
            ]
        )
    elif uri == "database://usage_data/sample":
        conn = db_engine.get_db_connection()
        sample_results = conn.execute("SELECT * FROM usage_data LIMIT 5").fetchall()
        sample_data = [dict(row) for row in sample_results]
        conn.close()
        
        return ReadResourceResult(
            contents=[
                TextContent(
                    type="text",
                    text=json.dumps(sample_data, indent=2)
                )
            ]
        )
    else:
        raise ValueError(f"Unknown resource: {uri}")

async def main():
    """Main entry point for the MCP server."""
    print(f"🚀 Starting {SERVER_NAME} v{SERVER_VERSION}")
    print("📡 MCP server ready for connections...")
    
    # Run the server using stdio transport
    async with stdio_server() as streams:
        await server.run(
            streams[0],  # stdin
            streams[1],  # stdout
            initialization_options={}
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 MCP server shutting down...")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)
