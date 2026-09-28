"""Проверки записи, ограничений и освобождения мест."""

from datetime import date, timedelta

import pytest

from bookings import cancel_booking, check_booking, create_booking
from workshops import available_seats, filter_workshops


def test_create_booking_uses_one_seat(state):
    booking = create_booking(
        state["workshops"], state["bookings"], 1, "Аня", 12,
    )
    assert booking.status == "active"
    assert available_seats(state["workshops"][0], state["bookings"]) == 1


def test_full_workshop_cannot_be_overbooked(state):
    for name in ("Аня", "Иван"):
        create_booking(state["workshops"], state["bookings"], 1, name, 18)
    with pytest.raises(ValueError, match="Свободных мест нет"):
        create_booking(state["workshops"], state["bookings"], 1, "Оля", 18)
    assert len(state["bookings"]) == 2
    result = list(filter_workshops(state["workshops"], state["bookings"], 18))
    assert result == []


def test_duplicate_participant_forbidden(state):
    create_booking(state["workshops"], state["bookings"], 1, "Аня", 18)
    with pytest.raises(ValueError, match="уже записан"):
        create_booking(state["workshops"], state["bookings"], 1, " АНЯ ", 18)


def test_cancel_frees_seat_and_keeps_history(state):
    create_booking(state["workshops"], state["bookings"], 1, "Аня", 18)
    cancel_booking(state["bookings"], 1)
    assert state["bookings"][0].status == "cancelled"
    assert available_seats(state["workshops"][0], state["bookings"]) == 2
    new = create_booking(state["workshops"], state["bookings"], 1, "Аня", 18)
    assert new.id == 2
    with pytest.raises(ValueError, match="уже отменена"):
        cancel_booking(state["bookings"], 1)


@pytest.mark.parametrize("name, age", [("", 18), ("Аня", 11), ("Аня", 121)])
def test_invalid_participant_rejected(state, name, age):
    with pytest.raises(ValueError):
        create_booking(state["workshops"], state["bookings"], 1, name, age)
    assert state["bookings"] == []


def test_past_date_rejected(state):
    workshop = state["workshops"][0]
    workshop.date = (date.today() - timedelta(days=1))
    assert "прошла" in check_booking(workshop, [], "Аня", 18)


def test_unknown_ids_rejected(state):
    with pytest.raises(ValueError, match="не найдено"):
        create_booking(state["workshops"], [], 99, "Аня", 18)
    with pytest.raises(ValueError, match="не найдена"):
        cancel_booking([], 99)
