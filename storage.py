"""Проверка целостности, загрузка и сохранение состояния в JSON."""

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from workshops import available_seats, get_workshop, validate_workshop


def validate_state(state: dict) -> None:
    """Отклонить повреждённые данные и несогласованные записи."""
    if not isinstance(state, dict) or set(state) != {"workshops", "bookings"}:
        raise ValueError("Ожидаются разделы workshops и bookings.")
    if not all(isinstance(items, list) for items in state.values()):
        raise ValueError("Занятия и записи должны храниться в списках.")
    ids = set()
    for workshop in state["workshops"]:
        if not isinstance(workshop, dict):
            raise ValueError("Занятие должно быть словарём.")
        validate_workshop(workshop)
        if workshop["id"] in ids:
            raise ValueError("Повторяется ID занятия.")
        ids.add(workshop["id"])
    booking_ids = set()
    participants = set()
    for booking in state["bookings"]:
        if not isinstance(booking, dict):
            raise ValueError("Запись должна быть словарём.")
        for key in ("id", "workshop_id", "user_age"):
            if type(booking.get(key)) is not int:
                raise ValueError(f"Поле записи {key} должно быть целым.")
        if booking["id"] < 1 or booking["id"] in booking_ids:
            raise ValueError("Некорректный или повторяющийся ID записи.")
        booking_ids.add(booking["id"])
        if booking["workshop_id"] not in ids:
            raise ValueError("Запись ссылается на отсутствующее занятие.")
        name = booking.get("user_name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Не указано имя участника.")
        if not 0 <= booking["user_age"] <= 120:
            raise ValueError("Некорректный возраст участника.")
        workshop = get_workshop(state["workshops"], booking["workshop_id"])
        if booking["user_age"] < workshop["minimum_age"]:
            raise ValueError("Возраст участника ниже ограничения занятия.")
        if booking.get("status") not in ("active", "cancelled"):
            raise ValueError("Некорректный статус записи.")
        if booking["status"] == "active":
            person = (
                booking["workshop_id"], name.strip().casefold(),
                booking["user_age"],
            )
            if person in participants:
                raise ValueError("Участник записан на занятие дважды.")
            participants.add(person)
    for workshop in state["workshops"]:
        if available_seats(workshop, state["bookings"]) < 0:
            raise ValueError("Число записей превышает вместимость занятия.")


def load_state(filename: Path) -> dict:
    """Прочитать JSON; отсутствие файла означает пустой новый каталог."""
    try:
        with filename.open(encoding="utf-8") as stream:
            state = json.load(stream)
    except FileNotFoundError:
        return {"workshops": [], "bookings": []}
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"Не удалось прочитать JSON: {error}") from error
    validate_state(state)
    return state


def save_state(filename: Path, state: dict) -> None:
    """Атомарно заменить JSON; при ошибке оставить исходный файл."""
    validate_state(state)
    filename.parent.mkdir(parents=True, exist_ok=True)
    scratch = Path(__file__).resolve().parent / "мусор" / "runtime"
    scratch.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=scratch, delete=False,
            suffix=".json",
        ) as stream:
            temporary = Path(stream.name)
            json.dump(state, stream, ensure_ascii=False, indent=2,
                      allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, filename)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
