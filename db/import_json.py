"""перенос занятий и записей из JSON в SQLite

запуск из корня проекта: python -m db.import_json
"""

import sqlite3
from pathlib import Path

from db.database import DATA_DIR, DB_PATH, SCHEMA_PATH, get_connection
from storage import read_items


def create_schema(conn: sqlite3.Connection) -> None:
    """создать таблицы, если их ещё нет"""
    with open(SCHEMA_PATH, encoding="utf-8") as file:
        conn.executescript(file.read())


def clear_tables(conn: sqlite3.Connection) -> None:
    """удалить старые данные, чтобы импорт можно было запускать повторно"""
    # сначала таблицы со ссылками, потом таблицы, на которые ссылаются
    conn.execute("DELETE FROM bookings")
    conn.execute("DELETE FROM users")
    conn.execute("DELETE FROM workshops")
    conn.execute("DELETE FROM masters")


def import_masters(conn: sqlite3.Connection, workshops: list[dict]) -> None:
    names = sorted({workshop["master"] for workshop in workshops})
    conn.executemany(
        "INSERT INTO masters (name) VALUES (?)",
        [(name,) for name in names],
    )


def import_workshops(conn: sqlite3.Connection, workshops: list[dict]) -> None:
    # master_id находится подзапросом по имени мастера
    conn.executemany(
        """
        INSERT INTO workshops (
            id, name, master_id, date, price, capacity, minimum_age
        )
        VALUES (?, ?, (SELECT id FROM masters WHERE name = ?), ?, ?, ?, ?)
        """,
        [
            (
                workshop["id"],
                workshop["name"],
                workshop["master"],
                workshop["date"],
                workshop["price"],
                workshop["capacity"],
                workshop["minimum_age"],
            )
            for workshop in workshops
        ],
    )


def import_users(conn: sqlite3.Connection, bookings: list[dict]) -> None:
    # у участника может быть несколько записей, в таблицу он попадает раз
    users = sorted({
        (booking["user_name"], booking["user_age"]) for booking in bookings
    })
    conn.executemany("INSERT INTO users (name, age) VALUES (?, ?)", users)


def import_bookings(conn: sqlite3.Connection, bookings: list[dict]) -> None:
    conn.executemany(
        """
        INSERT INTO bookings (id, workshop_id, user_id, status)
        VALUES (
            ?, ?, (SELECT id FROM users WHERE name = ? AND age = ?), ?
        )
        """,
        [
            (
                booking["id"],
                booking["workshop_id"],
                booking["user_name"],
                booking["user_age"],
                booking["status"],
            )
            for booking in bookings
        ],
    )


def import_data(data_dir: Path = DATA_DIR, db_path: Path = DB_PATH) -> None:
    """перенести оба JSON-файла в базу одной транзакцией"""
    workshops = read_items(data_dir / "workshops.json")
    bookings = read_items(data_dir / "bookings.json")

    conn = get_connection(db_path)
    try:
        create_schema(conn)
        clear_tables(conn)
        # порядок важен: сначала то, на что ссылаются внешние ключи
        import_masters(conn, workshops)
        import_workshops(conn, workshops)
        import_users(conn, bookings)
        import_bookings(conn, bookings)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import_data()
    print(f"Данные перенесены в {DB_PATH}")
