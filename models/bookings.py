"""Класс записи и функции работы с коллекцией записей."""

from __future__ import annotations

from .users import User
from .validation import checked_int
from .workshops import Workshop, get_workshop


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


def check_booking(
    workshop: Workshop, bookings: list[Booking], user_name: str, user_age: int,
) -> str:
    """Вернуть причину отказа или пустую строку (сценарий ПР1)."""
    try:
        user = User(user_name, user_age)
    except ValueError as error:
        return str(error)
    return workshop.check_booking(bookings, user)


def create_booking(
    workshops: list[Workshop], bookings: list[Booking], workshop_id: int,
    user_name: str, user_age: int,
) -> Booking:
    """Проверить доступность и добавить запись с уникальным ID."""
    workshop = get_workshop(workshops, workshop_id)
    user = User(user_name, user_age)
    reason = workshop.check_booking(bookings, user)
    if reason:
        raise ValueError(reason)
    booking = Booking(
        max((item.id for item in bookings), default=0) + 1, workshop, user,
    )
    bookings.append(booking)
    return booking


def cancel_booking(bookings: list[Booking], booking_id: int) -> Booking:
    """Найти запись и отменить её методом объекта."""
    for booking in bookings:
        if booking.id == booking_id:
            booking.cancel()
            return booking
    raise ValueError("Запись с таким ID не найдена.")
