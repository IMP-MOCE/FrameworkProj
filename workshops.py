"""Просмотр, поиск и добавление творческих занятий."""

from collections.abc import Iterator
from datetime import date
from math import isfinite


def validate_workshop(workshop: dict) -> None:
    """Проверить обязательные поля занятия; при ошибке вызвать ValueError."""
    for key in ("id", "capacity", "minimum_age"):
        if type(workshop.get(key)) is not int:
            raise ValueError(f"Поле {key} должно быть целым числом.")
    if workshop["id"] < 1 or workshop["capacity"] < 1:
        raise ValueError("ID и вместимость должны быть положительными.")
    if not 0 <= workshop["minimum_age"] <= 120:
        raise ValueError("Минимальный возраст должен быть от 0 до 120.")
    for key in ("name", "master"):
        value = workshop.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Поле {key} не должно быть пустым.")
    price = workshop.get("price")
    if type(price) not in (int, float) or not 0 <= price <= 1_000_000:
        raise ValueError("Цена должна быть от 0 до 1000000 рублей.")
    if not isfinite(price):
        raise ValueError("Цена должна быть конечным неотрицательным числом.")
    day = workshop.get("date")
    if not isinstance(day, str):
        raise ValueError("Дата должна быть строкой ГГГГ-ММ-ДД.")
    try:
        parsed = date.fromisoformat(day)
    except ValueError:
        raise ValueError("Некорректная дата занятия.") from None
    if parsed.isoformat() != day:
        raise ValueError("Дата должна иметь формат ГГГГ-ММ-ДД.")


def get_workshop(workshops: list[dict], workshop_id: int) -> dict:
    """Найти занятие по ID или сообщить, что оно не найдено."""
    for workshop in workshops:
        if workshop["id"] == workshop_id:
            return workshop
    raise ValueError("Занятие с таким ID не найдено.")


def add_workshop(
    workshops: list[dict], name: str, master: str, workshop_date: date,
    price: float, capacity: int, minimum_age: int,
) -> dict:
    """Добавить занятие с уникальным ID после проверки его данных."""
    workshop = {
        "id": max((item["id"] for item in workshops), default=0) + 1,
        "name": name.strip(), "master": master.strip(),
        "date": workshop_date.isoformat(), "price": price,
        "capacity": capacity, "minimum_age": minimum_age,
    }
    validate_workshop(workshop)
    if workshop_date < date.today():
        raise ValueError("Нельзя добавить занятие на прошедшую дату.")
    workshops.append(workshop)
    return workshop


def find_workshops(workshops: list[dict], query: str) -> list[dict]:
    """Найти занятия по части названия без учёта регистра."""
    query = query.strip().casefold()
    return [item for item in workshops if query in item["name"].casefold()]


def available_seats(workshop: dict, bookings: list[dict]) -> int:
    """Вычесть активные записи из вместимости занятия."""
    occupied = sum(
        1 for booking in bookings
        if booking["workshop_id"] == workshop["id"]
        and booking["status"] == "active"
    )
    return workshop["capacity"] - occupied


def filter_workshops(
    workshops: list[dict], bookings: list[dict], age: int,
) -> Iterator[dict]:
    """Выдавать генератором будущие доступные занятия для возраста."""
    if not 0 <= age <= 120:
        raise ValueError("Возраст должен быть от 0 до 120.")
    for workshop in workshops:
        if (
            date.fromisoformat(workshop["date"]) >= date.today()
            and age >= workshop["minimum_age"]
            and available_seats(workshop, bookings) > 0
        ):
            yield workshop


def sort_workshops(workshops: list[dict], key: str) -> list[dict]:
    """Вернуть занятия по возрастанию цены или даты без изменения списка."""
    if key not in ("price", "date"):
        raise ValueError("Сортировка возможна по цене или дате.")
    return sorted(workshops, key=lambda workshop: workshop[key])
