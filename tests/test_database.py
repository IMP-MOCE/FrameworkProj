"""проверки базы SQLite: схема, перенос из JSON и внешние ключи"""

import sqlite3

import pytest

from db.database import get_connection
from db.import_json import import_data
from models.bookings import cancel_booking, create_booking
from storage import save_state


@pytest.fixture
def db_path(tmp_path, state):
    """временные JSON с двумя записями одного участника и их перенос в базу"""
    save_state(tmp_path, state, "workshops")
    create_booking(state["workshops"], state["bookings"], 1, "Мария", 18)
    cancel_booking(state["bookings"], 1)
    create_booking(state["workshops"], state["bookings"], 1, "Мария", 18)
    save_state(tmp_path, state, "bookings")
    path = tmp_path / "studio.sqlite"
    import_data(tmp_path, path)
    return path


def count(path, query):
    conn = get_connection(path)
    try:
        return conn.execute(query).fetchone()[0]
    finally:
        conn.close()


def test_import_creates_tables_and_rows(db_path):
    conn = get_connection(db_path)
    tables = {
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'",
        )
    }
    workshop = conn.execute(
        """
        SELECT workshops.name, masters.name, workshops.price
        FROM workshops
        JOIN masters ON workshops.master_id = masters.id
        """,
    ).fetchone()
    conn.close()
    assert tables == {"masters", "workshops", "users", "bookings"}
    assert workshop == ("Роспись кружки", "Анна", 1500.0)
    # участник с двумя записями хранится один раз
    assert count(db_path, "SELECT COUNT(*) FROM users") == 1
    assert count(db_path, "SELECT COUNT(*) FROM bookings") == 2


def test_import_can_be_repeated(db_path):
    import_data(db_path.parent, db_path)
    assert count(db_path, "SELECT COUNT(*) FROM workshops") == 1
    assert count(db_path, "SELECT COUNT(*) FROM masters") == 1
    assert count(db_path, "SELECT COUNT(*) FROM bookings") == 2


def test_foreign_keys_are_checked(db_path):
    conn = get_connection(db_path)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO bookings (workshop_id, user_id) VALUES (?, ?)",
            [999, 1],
        )
    conn.close()


def test_status_is_limited_by_check(db_path):
    conn = get_connection(db_path)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE bookings SET status = ? WHERE id = 1", ["done"])
    conn.close()


def test_failed_import_keeps_old_data(db_path):
    broken = db_path.parent / "broken"
    broken.mkdir()
    (broken / "workshops.json").write_text("[]", encoding="utf-8")
    (broken / "bookings.json").write_text(
        '[{"id": 1, "workshop_id": 999, "user_name": "Мария",'
        ' "user_age": 18, "status": "active"}]',
        encoding="utf-8",
    )
    with pytest.raises(sqlite3.IntegrityError):
        import_data(broken, db_path)
    assert count(db_path, "SELECT COUNT(*) FROM workshops") == 1
    assert count(db_path, "SELECT COUNT(*) FROM bookings") == 2
