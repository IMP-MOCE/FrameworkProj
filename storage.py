"""Проверка целостности и хранение объектов в двух JSON-файлах."""

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal, TypedDict

from models import Booking, Workshop


class State(TypedDict):
    """Коллекции объектов; общий контейнер не является сущностью."""

    workshops: list[Workshop]
    bookings: list[Booking]


def validate_state(state: State) -> None:
    """Проверить объекты, уникальность ID, связи и вместимость."""
    ids = {}
    for workshop in state["workshops"]:
        if not isinstance(workshop, Workshop):
            raise ValueError("Ожидается объект занятия.")
        Workshop.from_data(workshop.to_data())
        if workshop.id in ids:
            raise ValueError("Повторяется ID занятия.")
        ids[workshop.id] = workshop
    booking_ids = set()
    participants = set()
    for booking in state["bookings"]:
        if not isinstance(booking, Booking):
            raise ValueError("Ожидается объект записи.")
        Booking.from_data(booking.to_data(), ids)
        if ids.get(booking.workshop.id) is not booking.workshop:
            raise ValueError("Запись должна ссылаться на объект из каталога.")
        if booking.id in booking_ids:
            raise ValueError("Повторяется ID записи.")
        booking_ids.add(booking.id)
        if booking.status == "active":
            person = (booking.workshop.id, *booking.user.identity())
            if person in participants:
                raise ValueError("Участник записан на занятие дважды.")
            participants.add(person)
    for workshop in state["workshops"]:
        if workshop.available_seats(state["bookings"]) < 0:
            raise ValueError("Число записей превышает вместимость занятия.")


def read_items(filename: Path) -> list[dict]:
    """Прочитать список JSON; отсутствующий файл означает пустой список."""
    try:
        with filename.open(encoding="utf-8") as stream:
            items = json.load(stream)
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"Не удалось прочитать {filename.name}: {error}")
    if not isinstance(items, list) or not all(
        isinstance(item, dict) for item in items
    ):
        raise ValueError(f"{filename.name}: ожидается список объектов.")
    return items


def load_state(directory: Path) -> State:
    """Сначала загрузить занятия, затем восстановить ссылки записей."""
    workshops = [
        Workshop.from_data(item)
        for item in read_items(directory / "workshops.json")
    ]
    ids = {item.id: item for item in workshops}
    bookings = [
        Booking.from_data(item, ids)
        for item in read_items(directory / "bookings.json")
    ]
    state: State = {"workshops": workshops, "bookings": bookings}
    validate_state(state)
    return state


def save_state(
    directory: Path, state: State,
    entity: Literal["workshops", "bookings"],
) -> None:
    """Проверить состояние и атомарно сохранить одну изменённую сущность.

    Файл второй сущности должен совпадать с состоянием в памяти. Поэтому
    отдельное сохранение не может создать несогласованную пару файлов.
    """
    if entity not in ("workshops", "bookings"):
        raise ValueError("Неизвестная сущность.")
    validate_state(state)
    other = "bookings" if entity == "workshops" else "workshops"
    expected = [item.to_data() for item in state[other]]
    if read_items(directory / f"{other}.json") != expected:
        raise ValueError(
            "Связанные данные изменились. Перезапустите программу.",
        )
    filename = directory / f"{entity}.json"
    directory.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=directory, delete=False,
            prefix=f".{entity}-", suffix=".tmp",
        ) as stream:
            temporary = Path(stream.name)
            json.dump(
                [item.to_data() for item in state[entity]], stream,
                ensure_ascii=False, indent=2, allow_nan=False,
            )
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, filename)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
