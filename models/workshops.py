"""Класс занятия и функции работы с коллекцией занятий."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from datetime import date
from math import isfinite
from typing import TYPE_CHECKING

from .masters import Master
from .users import User
from .validation import checked_int, checked_name

if TYPE_CHECKING:
    from .bookings import Booking


class Workshop:
    """Занятие с ограничениями по возрасту, дате и вместимости."""

    def __init__(
        self, workshop_id: int, name: str, master: Master,
        workshop_date: date, price: float, capacity: int, minimum_age: int,
    ) -> None:
        self.id = checked_int(workshop_id, 1, 1_000_000_000)
        self.name = checked_name(name)
        if not isinstance(master, Master):
            raise ValueError("Ожидается объект мастера.")
        if type(workshop_date) is not date:
            raise ValueError("Ожидается дата занятия.")
        if isinstance(price, bool) or not isinstance(price, (int, float)):
            raise ValueError("Цена должна быть числом.")
        if not 0 <= price <= 1_000_000 or not isfinite(price):
            raise ValueError("Цена должна быть от 0 до 1000000 рублей.")
        self.master = master
        self.date = workshop_date
        self.price = price
        self.capacity = checked_int(capacity, 1, 10000)
        self.minimum_age = checked_int(minimum_age, 0, 120)

    def available_seats(self, bookings: Iterable[Booking]) -> int:
        """Вычесть активные записи из вместимости."""
        return self.capacity - sum(
            booking.workshop.id == self.id and booking.status == "active"
            for booking in bookings
        )

    def check_booking(self, bookings: Iterable[Booking], user: User) -> str:
        """Вернуть причину отказа или пустую строку."""
        if user.age < self.minimum_age:
            return f"Занятие доступно с {self.minimum_age} лет."
        if self.date < date.today():
            return "Дата занятия уже прошла."
        active = [item for item in bookings if item.status == "active"
                  and item.workshop.id == self.id]
        if any(item.user.identity() == user.identity() for item in active):
            return "Этот участник уже записан на занятие."
        if len(active) >= self.capacity:
            return "Свободных мест нет."
        return ""

    def to_data(self) -> dict:
        """Получить обычные данные для JSON."""
        return {
            "id": self.id, "name": self.name, "master": self.master.name,
            "date": self.date.isoformat(), "price": self.price,
            "capacity": self.capacity, "minimum_age": self.minimum_age,
        }

    @classmethod
    def from_data(cls, data: dict) -> Workshop:
        """Восстановить занятие, в том числе с прошедшей датой."""
        try:
            day = date.fromisoformat(data["date"])
            if day.isoformat() != data["date"]:
                raise ValueError("Дата должна иметь формат ГГГГ-ММ-ДД.")
            return cls(
                data["id"], data["name"], Master(data["master"]), day,
                data["price"], data["capacity"], data["minimum_age"],
            )
        except (KeyError, TypeError, AttributeError) as error:
            raise ValueError("Некорректные данные занятия.") from error

    def __str__(self) -> str:
        return (f"[{self.id}] {self.name}; мастер: {self.master}; "
                f"{self.date:%d.%m.%Y}; {self.price:.2f} руб.")


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
