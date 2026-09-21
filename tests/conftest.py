"""Независимые исходные данные для каждого теста."""

from datetime import date, timedelta

import pytest

from workshops import add_workshop


@pytest.fixture
def state():
    """Создать одно будущее занятие с двумя местами."""
    result = {"workshops": [], "bookings": []}
    add_workshop(
        result["workshops"], "Роспись кружки", "Анна",
        date.today() + timedelta(days=7), 1500.0, 2, 12,
    )
    return result
