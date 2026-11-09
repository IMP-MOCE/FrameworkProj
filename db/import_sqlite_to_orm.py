"""Повторяемый перенос ПР7 в ORM с проверкой конфликтов и связей."""

from contextlib import closing
from datetime import date
from decimal import Decimal
from pathlib import Path
import sqlite3

from django.conf import settings
from django.db import transaction

from bookings.models import Booking
from masters.models import Master
from users.models import User
from workshops.models import Workshop


def store(model, row_id, values):
    """Создать строку или проверить совпадение при повторном переносе."""
    obj = model.objects.filter(pk=row_id).first()
    if obj is not None:
        if any(getattr(obj, key) != value for key, value in values.items()):
            raise ValueError(f"Конфликт {model.__name__} #{row_id}.")
        return
    obj = model(pk=row_id, **values)
    obj.full_clean()
    obj.save()


def import_data(source=None):
    source = Path(source or settings.BASE_DIR / "data/studio.sqlite").resolve()
    if not source.is_file():
        raise ValueError(f"Исходная база не найдена: {source}")
    if source == Path(settings.DATABASES["default"]["NAME"]).resolve():
        raise ValueError("Исходная и целевая базы должны различаться.")
    connection = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
    with closing(connection) as conn:
        conn.row_factory = sqlite3.Row
        tables = {
            table: conn.execute(
                f"SELECT * FROM {table} ORDER BY id",
            ).fetchall()
            for table in ("masters", "users", "workshops", "bookings")
        }
    with transaction.atomic():
        for row in tables["masters"]:
            store(Master, row["id"], {"name": row["name"]})
        for row in tables["users"]:
            store(User, row["id"], {"name": row["name"], "age": row["age"]})
        for row in tables["workshops"]:
            store(Workshop, row["id"], {
                "name": row["name"], "master_id": row["master_id"],
                "date": date.fromisoformat(row["date"]),
                "price": Decimal(str(row["price"])),
                "capacity": row["capacity"], "minimum_age": row["minimum_age"],
                "description": row["description"],
            })
        for row in tables["bookings"]:
            store(Booking, row["id"], {
                "workshop_id": row["workshop_id"], "user_id": row["user_id"],
                "status": row["status"],
            })
    return {table: len(rows) for table, rows in tables.items()}
