"""Объекты предметной области сервиса творческих занятий."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from math import isfinite


def checked_name(value: str) -> str:
    """Проверить имя или название и убрать крайние пробелы."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Имя или название не должно быть пустым.")
    return value.strip()


def checked_int(value: int, minimum: int, maximum: int) -> int:
    """Проверить целое число, исключая логические значения."""
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"Ожидается целое число от {minimum} до {maximum}.")
    return value


class User:
    """Участник, определяемый именем и возрастом."""

    def __init__(self, name: str, age: int) -> None:
        self.name = checked_name(name)
        self.age = checked_int(age, 0, 120)

    def identity(self) -> tuple[str, int]:
        """Получить ключ участника для проверки повторной записи."""
        return self.name.strip().casefold(), self.age

    def __str__(self) -> str:
        return f"{self.name}, {self.age} лет"


class Master:
    """Ведущий творческого занятия."""

    def __init__(self, name: str) -> None:
        self.name = checked_name(name)

    def __str__(self) -> str:
        return self.name


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


class Booking:
    """Запись связывает объекты участника и занятия и хранит статус."""

    def __init__(
        self, booking_id: int, workshop: Workshop, user: User,
        status: str = "active",
    ) -> None:
        self.id = checked_int(booking_id, 1, 1_000_000_000)
        if not isinstance(workshop, Workshop) or not isinstance(user, User):
            raise ValueError("Запись должна связывать занятие и участника.")
        if status not in ("active", "cancelled"):
            raise ValueError("Некорректный статус записи.")
        if user.age < workshop.minimum_age:
            raise ValueError("Возраст участника ниже ограничения занятия.")
        self.workshop = workshop
        self.user = user
        self._status = status

    @property
    def status(self) -> str:
        """Статус изменяется через метод отмены."""
        return self._status

    def cancel(self) -> None:
        """Отменить запись, сохранив её в истории."""
        if self.status == "cancelled":
            raise ValueError("Запись уже отменена.")
        self._status = "cancelled"

    def to_data(self) -> dict:
        """Сохранить ID занятия и данные участника."""
        return {
            "id": self.id, "workshop_id": self.workshop.id,
            "user_name": self.user.name, "user_age": self.user.age,
            "status": self.status,
        }

    @classmethod
    def from_data(cls, data: dict, workshops: dict[int, Workshop]) -> Booking:
        """Восстановить ссылку на занятие из загруженного каталога."""
        try:
            workshop_id = checked_int(data["workshop_id"], 1, 1_000_000_000)
            if workshop_id not in workshops:
                raise ValueError("Запись ссылается на отсутствующее занятие.")
            return cls(
                data["id"], workshops[workshop_id],
                User(data["user_name"], data["user_age"]), data["status"],
            )
        except (KeyError, TypeError) as error:
            raise ValueError("Некорректные данные записи.") from error

    def __str__(self) -> str:
        status = "активна" if self.status == "active" else "отменена"
        return (f"[{self.id}] {self.user} — {self.workshop.name}; "
                f"{self.workshop.date:%d.%m.%Y}; {status}")
