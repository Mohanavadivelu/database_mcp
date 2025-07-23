# database/query_engine.py
# Shared database query logic for both Flask web interface and MCP server

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
import sqlite3
import json
import openai
from typing import Dict, List, Any, Tuple, Optional
from dotenv import load_dotenv

# Import our modules
from database.connection import get_db_connection
from core.prompts import get_sql_generation_prompt, get_data_interpretation_prompt

# Load environment variables
load_dotenv()

# Database configuration
DATABASE = os.path.join(os.path.dirname(__file__), 'usage.db')

# Token limit considerations for LLM processing
MAX_ROWS_FOR_LLM_SUMMARY = 200  # Balanced limit for good performance and comprehensive analysis

class DatabaseQueryEngine:
    """
    Core database query engine that handles natural language to SQL conversion
    and data interpretation. Used by both Flask web interface and MCP server.
    """
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        try:
            openai.api_key = self.openai_api_key
            self.client = openai.OpenAI()
        except Exception as e:
            raise ValueError(f"Error initializing OpenAI client: {e}")
    
    def get_db_connection(self) -> sqlite3.Connection:
        """Get database connection using the centralized connection module."""
        return get_db_connection()
    
    def validate_question(self, question: str) -> Tuple[bool, Optional[str]]:
        """
        Validate user question for security and basic requirements.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not question or not question.strip():
            return False, "No question provided"
        
        # Security check - prevent SQL injection and harmful operations
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE']
        if any(keyword in question.upper() for keyword in dangerous_keywords):
            return False, "Potentially harmful question detected"
        
        return True, None
    
    def get_database_schema(self) -> str:
        """Retrieve database schema for the usage_data table."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='usage_data'")
        schema_result = cursor.fetchone()
        conn.close()
        
        if not schema_result:
            raise ValueError("Database schema not found for usage_data table")
        
        return schema_result[0]
    
    def generate_sql_from_question(self, question: str) -> str:
        """
        Convert natural language question to SQL using LLM.
        
        Args:
            question: Natural language question from user
            
        Returns:
            Generated SQL query string
            
        Raises:
            ValueError: If LLM generates unsafe query
            openai.APIError: If OpenAI API call fails
        """
        print("🤖 Converting natural language to SQL using LLM...")
        
        # Import prompts (assuming they exist)
        try:
            from core.prompts import get_sql_generation_prompt
        except ImportError:
            # Fallback basic prompt if prompts.py doesn't exist
            schema = self.get_database_schema()
            sql_generation_prompt = f"""
            You are a SQL expert. Given the database schema and a natural language question, 
            generate ONLY a SELECT SQL query. Do not include any explanations.
            
            Database Schema:
            {schema}
            
            Rules:
            1. Only generate SELECT queries
            2. Use proper SQL syntax for SQLite
            3. Return only the SQL query, no markdown or explanations
            """
        else:
            schema = self.get_database_schema()
            sql_generation_prompt = get_sql_generation_prompt(schema)
        
        # Make API call to generate SQL
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": sql_generation_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.0  # Use deterministic output for SQL generation
        )
        
        # Extract and clean the generated SQL
        generated_sql = completion.choices[0].message.content.strip().replace('`', '')
        print(f"Generated SQL: {generated_sql}")
        
        # Security validation - ensure only SELECT queries are executed
        if not generated_sql.upper().startswith("SELECT"):
            raise ValueError("LLM generated a non-SELECT query. Aborting for safety.")
        
        return generated_sql
    
    def execute_sql_query(self, sql: str) -> List[sqlite3.Row]:
        """
        Execute SQL query and return results.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            List of database rows
        """
        print("💾 Executing SQL query...")
        
        conn = self.get_db_connection()
        try:
            results = conn.execute(sql).fetchall()
            print(f"Query returned {len(results)} rows")
            return results
        finally:
            conn.close()
    
    def interpret_data_with_llm(self, question: str, data: List[Dict[str, Any]]) -> str:
        """
        Convert query results to human-readable response using LLM.
        
        Args:
            question: Original user question
            data: Query results as list of dictionaries
            
        Returns:
            Human-readable interpretation of the data
        """
        print("📝 Converting data to human-readable response...")
        
        # Prepare data for LLM interpretation
        data_json = json.dumps(data, indent=2)
        
        # Try to import custom prompt, fallback to basic one
        try:
            from core.prompts import get_data_interpretation_prompt
            interpretation_prompt = get_data_interpretation_prompt(question, data_json)
        except ImportError:
            interpretation_prompt = f"""
            Analyze the following data and provide a clear, natural language answer to the user's question.
            
            User Question: {question}
            
            Data:
            {data_json}
            
            Please provide a concise, helpful summary of what this data shows in relation to the user's question.
            """
        
        # Generate human-readable interpretation
        final_completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": "You are a helpful data analyst assistant who provides clear, natural language answers based on data."},
                {"role": "user", "content": interpretation_prompt}
            ],
            temperature=0.5  # Allow some creativity in response formatting
        )
        
        return final_completion.choices[0].message.content.strip()
    
    def process_natural_language_query(self, question: str) -> Dict[str, Any]:
        """
        Main method to process a natural language question and return results.
        
        This implements the complete pipeline:
        1. Validate input
        2. Convert to SQL
        3. Execute query
        4. Process results
        5. Generate human-readable response
        
        Args:
            question: Natural language question from user
            
        Returns:
            Dictionary containing:
            - answer: Human-readable response
            - data: Raw query results
            - question: Original question
            - sql: Generated SQL (for debugging)
            
        Raises:
            ValueError: For validation errors or unsafe queries
            Exception: For database or API errors
        """
        # Step 1: Validate input
        print("🔍 Step 1: Validating input...")
        is_valid, error_msg = self.validate_question(question)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Step 2: Generate SQL from question
        print("📋 Step 2: Generating SQL from question...")
        sql = self.generate_sql_from_question(question)
        
        # Step 3: Execute SQL query
        print("💾 Step 3: Executing SQL query...")
        results = self.execute_sql_query(sql)
        
        # Step 4: Handle empty results
        if not results:
            return {
                'answer': "I couldn't find any data that answers your question.",
                'data': [],
                'question': question,
                'sql': sql
            }
        
        # Step 5: Convert results to list of dictionaries
        data = [dict(row) for row in results]
        
        # Step 6: Handle large result sets (circuit breaker)
        print("🔄 Step 4: Checking result set size...")
        if len(results) > MAX_ROWS_FOR_LLM_SUMMARY:
            total_rows = len(results)
            sample_data = data[:10]
            human_answer = (
                f"Your query returned {total_rows} rows, which is too large to summarize.\n"
                f"Please try a more specific question (e.g., 'who were the top 5 most active users last week?').\n\n"
                f"Here is a sample of the first 10 rows:\n"
                f"{json.dumps(sample_data, indent=2)}"
            )
            return {
                'answer': human_answer,
                'data': data,
                'question': question,
                'sql': sql
            }
        
        # Step 7: Generate human-readable interpretation
        print("📝 Step 5: Generating human-readable response...")
        human_answer = self.interpret_data_with_llm(question, data)
        
        # Step 8: Return complete response
        print("✅ Step 6: Returning successful response...")
        return {
            'answer': human_answer,
            'data': data,
            'question': question,
            'sql': sql
        }

# Convenience function for backward compatibility
def process_database_query(question: str) -> Dict[str, Any]:
    """
    Convenience function to process a database query.
    Creates a new DatabaseQueryEngine instance and processes the query.
    """
    engine = DatabaseQueryEngine()
    return engine.process_natural_language_query(question)
