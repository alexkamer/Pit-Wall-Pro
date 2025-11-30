"""Database connection and utilities."""

import sqlite3
import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent.parent / "f1_data.db"


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get a database connection.

    Args:
        db_path: Path to the SQLite database file. Uses default if not provided.

    Returns:
        sqlite3.Connection: Database connection
    """
    if db_path is None:
        db_path = str(DEFAULT_DB_PATH)

    conn = sqlite3.Connection(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def initialize_database(db_path: Optional[str] = None) -> None:
    """Initialize the database with the schema.

    Args:
        db_path: Path to the SQLite database file. Uses default if not provided.
    """
    if db_path is None:
        db_path = str(DEFAULT_DB_PATH)

    # Read schema file
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, 'r') as f:
        schema = f.read()

    # Create database and execute schema
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema)
        conn.commit()
        logger.info(f"Database initialized at {db_path}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        conn.close()


def dict_factory(cursor, row):
    """Convert database row to dictionary."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
