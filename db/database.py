"""подключение к базе SQLite и выполнение запросов на чтение"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "studio.sqlite"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """открыть базу и включить проверку внешних ключей"""
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def fetch_all(query: str, params: list | tuple = ()) -> list[sqlite3.Row]:
    """выполнить SELECT и вернуть все строки"""
    conn = get_connection()
    # к полям строки можно обращаться по имени: row["name"]
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def fetch_one(query: str, params: list | tuple = ()) -> sqlite3.Row | None:
    """выполнить SELECT и вернуть первую строку или None"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(query, params).fetchone()
    finally:
        conn.close()
