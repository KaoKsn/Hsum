import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from fastapi import Request

# DATABASE CONFIGURATION

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database directory
DATABASE_DIR = BASE_DIR / "database"

# SQLite database file
DATABASE_PATH = DATABASE_DIR / "hospital.db"

# SQL initialization file
INIT_SQL_PATH = DATABASE_DIR / "init.sql"


# DATABASE CONNECTION
def get_connection() -> sqlite3.Connection:
    """
    Establishes and returns a connection to the SQLite database.
    Foreign key constraints are enabled for every connection.
    """

    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH, timeout=10.0, check_same_thread=False)

    # Return rows as dictionary-like objects
    conn.row_factory = sqlite3.Row

    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")

    # Wait for other transactions instead of immediately failing
    conn.execute("PRAGMA busy_timeout = 10000")

    return conn


# DATABASE INITIALIZATION
def initialize_database() -> None:
    """
    Initializes the database using init.sql.

    Creates all required tables and indexes if they
    do not already exist.
    """

    if not INIT_SQL_PATH.exists():
        raise FileNotFoundError(
            f"Database initialization file not found: {INIT_SQL_PATH}"
        )
    conn = get_connection()
    try:
        with conn:
            with open(INIT_SQL_PATH, "r", encoding="utf-8") as sql_file:
                sql_script = sql_file.read()
            conn.executescript(sql_script)
    finally:
        conn.close()


# FASTAPI DATABASE DEPENDENCY
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    FastAPI dependency.

    Provides a database connection to an endpoint
    and ensures that it is closed afterwards.

    Usage:

        @app.get("/example")
        def example(db = Depends(get_db)):
            ...
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


# TRANSACTION MANAGEMENT
@contextmanager
def get_transaction():
    """
    Provides a database connection with automatic
    transaction management.

    Commits changes if everything succeeds.
    Rolls back changes if an exception occurs.

    Usage:

        with get_transaction() as db:
            db.execute(...)
            db.execute(...)
    """
    conn = get_connection()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


# DATABASE HEALTH CHECK
def check_database() -> bool:
    """
    Checks whether the SQLite database is accessible.
    """
    try:
        conn = get_connection()
        try:
            result = conn.execute("SELECT 1").fetchone()
            return result is not None
        finally:
            conn.close()
    except sqlite3.Error:
        return False
