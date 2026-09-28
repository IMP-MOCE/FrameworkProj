"""Проверки объектов, композиции, методов и преобразования данных."""

from copy import deepcopy
from datetime import date, timedelta

import pytest

from bookings import create_booking
from models import Booking, Master, User, Workshop
from storage import load_state, save_state, validate_state


def test_objects_and_string_representations(state):
    workshop = state["workshops"][0]
    booking = create_booking(
        state["workshops"], state["bookings"], 1, " Аня ", 18,
    )
    assert isinstance(workshop, Workshop)
    assert isinstance(workshop.master, Master)
    assert isinstance(booking.user, User)
    assert booking.workshop is workshop
    assert booking.user.name == "Аня"
    assert "Аня, 18 лет" == str(booking.user)
    assert str(workshop.master) == "Анна"
    assert "Роспись кружки" in str(workshop)
    assert "1500.00" in str(workshop)
    assert "активна" in str(booking)
    booking.cancel()
    assert "отменена" in str(booking)
    assert workshop.available_seats(state["bookings"]) == 2
    with pytest.raises(AttributeError):
        booking.status = "active"


@pytest.mark.parametrize("name, age", [
    ("", 18), (None, 18), ("Аня", True), ("Аня", -1), ("Аня", 121),
])
def test_invalid_user(name, age):
    with pytest.raises(ValueError):
        User(name, age)


@pytest.mark.parametrize("price", [
    True, "500", -1, float("nan"), float("inf"), 10 ** 1000,
])
def test_invalid_price(state, price):
    data = state["workshops"][0].to_data()
    data["price"] = price
    with pytest.raises(ValueError):
        Workshop.from_data(data)


def test_direct_booking_validation(state):
    workshop = state["workshops"][0]
    with pytest.raises(ValueError):
        Booking(1, workshop, User("Аня", 5))
    with pytest.raises(ValueError):
        Booking(1, workshop, User("Аня", 18), "unknown")


def test_past_cancelled_booking_can_be_restored(tmp_path, state):
    workshop = state["workshops"][0]
    booking = create_booking(
        state["workshops"], state["bookings"], 1, "Аня", 18,
    )
    booking.cancel()
    workshop.date = date.today() - timedelta(days=1)
    save_state(tmp_path, {"workshops": [workshop], "bookings": []},
               "workshops")
    save_state(tmp_path, state, "bookings")
    restored = load_state(tmp_path)
    assert restored["bookings"][0].status == "cancelled"
    assert restored["bookings"][0].workshop is restored["workshops"][0]


def test_copy_preserves_internal_links_and_isolates_original(state):
    create_booking(state["workshops"], state["bookings"], 1, "Аня", 18)
    candidate = deepcopy(state)
    assert candidate["bookings"][0].workshop is candidate["workshops"][0]
    candidate["bookings"][0].cancel()
    assert state["bookings"][0].status == "active"


def test_detached_workshop_rejected(state):
    booking = create_booking(
        state["workshops"], state["bookings"], 1, "Аня", 18,
    )
    booking.workshop = deepcopy(booking.workshop)
    with pytest.raises(ValueError, match="объект из каталога"):
        validate_state(state)
