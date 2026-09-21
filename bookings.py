"""Проверка условий участия, создание и отмена записей."""

from datetime import date

from workshops import available_seats, get_workshop


def check_booking(
    workshop: dict, bookings: list[dict], user_name: str, user_age: int,
) -> str:
    """Вернуть причину отказа или пустую строку, если запись доступна."""
    if not user_name.strip():
        return "Имя не должно быть пустым."
    if type(user_age) is not int or not 0 <= user_age <= 120:
        return "Возраст должен быть целым числом от 0 до 120."
    if user_age < workshop["minimum_age"]:
        return f"Занятие доступно с {workshop['minimum_age']} лет."
    if date.fromisoformat(workshop["date"]) < date.today():
        return "Дата занятия уже прошла."
    for booking in bookings:
        if (
            booking["workshop_id"] == workshop["id"]
            and booking["status"] == "active"
            and booking["user_name"].casefold() == user_name.strip().casefold()
            and booking["user_age"] == user_age
        ):
            return "Этот участник уже записан на занятие."
    if available_seats(workshop, bookings) <= 0:
        return "Свободных мест нет."
    return ""


def create_booking(
    workshops: list[dict], bookings: list[dict], workshop_id: int,
    user_name: str, user_age: int,
) -> dict:
    """Проверить условия и добавить активную запись с уникальным ID."""
    workshop = get_workshop(workshops, workshop_id)
    reason = check_booking(workshop, bookings, user_name, user_age)
    if reason:
        raise ValueError(reason)
    booking = {
        "id": max((item["id"] for item in bookings), default=0) + 1,
        "workshop_id": workshop_id, "user_name": user_name.strip(),
        "user_age": user_age, "status": "active",
    }
    bookings.append(booking)
    return booking


def cancel_booking(bookings: list[dict], booking_id: int) -> dict:
    """Отменить активную запись, сохранив её ID и данные в истории."""
    for booking in bookings:
        if booking["id"] == booking_id:
            if booking["status"] == "cancelled":
                raise ValueError("Запись уже отменена.")
            booking["status"] = "cancelled"
            return booking
    raise ValueError("Запись с таким ID не найдена.")
