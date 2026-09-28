"""Функции работы с коллекцией творческих занятий."""

from collections.abc import Iterator
from datetime import date

from models import Booking, Master, Workshop, checked_int


def get_workshop(workshops: list[Workshop], workshop_id: int) -> Workshop:
    """Найти занятие по ID или сообщить, что оно не найдено."""
    for workshop in workshops:
        if workshop.id == workshop_id:
            return workshop
    raise ValueError("Занятие с таким ID не найдено.")


def add_workshop(
    workshops: list[Workshop], name: str, master: str, workshop_date: date,
    price: float, capacity: int, minimum_age: int,
) -> Workshop:
    """Добавить занятие с уникальным ID после проверки его данных."""
    workshop = Workshop(
        max((item.id for item in workshops), default=0) + 1,
        name, Master(master), workshop_date, price, capacity, minimum_age,
    )
    if workshop.date < date.today():
        raise ValueError("Нельзя добавить занятие на прошедшую дату.")
    workshops.append(workshop)
    return workshop


def find_workshops(workshops: list[Workshop], query: str) -> list[Workshop]:
    """Найти занятия по части названия без учёта регистра."""
    query = query.strip().casefold()
    return [item for item in workshops if query in item.name.casefold()]


def available_seats(workshop: Workshop, bookings: list[Booking]) -> int:
    """Вернуть остаток мест через метод занятия (сценарий ПР2)."""
    return workshop.available_seats(bookings)


def filter_workshops(
    workshops: list[Workshop], bookings: list[Booking], age: int,
) -> Iterator[Workshop]:
    """Выдавать генератором будущие доступные занятия для возраста."""
    checked_int(age, 0, 120)
    for workshop in workshops:
        if (workshop.date >= date.today()
                and age >= workshop.minimum_age
                and workshop.available_seats(bookings) > 0):
            yield workshop


def sort_workshops(workshops: list[Workshop], key: str) -> list[Workshop]:
    """Вернуть занятия по цене или дате без изменения исходного списка."""
    if key not in ("price", "date"):
        raise ValueError("Сортировка возможна по цене или дате.")
    return sorted(workshops, key=lambda workshop: getattr(workshop, key))
