"""Создание и поиск записей в коллекциях объектов."""

from models import Booking, User, Workshop
from workshops import get_workshop


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
