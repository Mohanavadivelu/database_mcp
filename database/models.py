"""
Database models and schema definitions.

This module defines the data models and database schema for the application.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import os

# Database configuration
DATABASE = os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'usage.db'))

@dataclass
class UsageRecord:
    """
    Represents a single usage record in the database.
    """
    id: Optional[int]
    user: str
    application_name: str
    duration_seconds: int
    timestamp: Optional[datetime] = None
    
    def to_dict(self):
        """Convert the usage record to a dictionary."""
        return {
            'id': self.id,
            'user': self.user,
            'application_name': self.application_name,
            'duration_seconds': self.duration_seconds,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    @classmethod
    def from_row(cls, row):
        """Create a UsageRecord from a database row."""
        return cls(
            id=row['id'],
            user=row['user'],
            application_name=row['application_name'],
            duration_seconds=row['duration_seconds'],
            timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else None
        )

@dataclass
class QueryResult:
    """
    Represents the result of a database query operation.
    """
    success: bool
    data: list
    message: str
    sql_query: Optional[str] = None
    row_count: int = 0
    
    def to_dict(self):
        """Convert the query result to a dictionary."""
        return {
            'success': self.success,
            'data': self.data,
            'message': self.message,
            'sql_query': self.sql_query,
            'row_count': self.row_count
        }
