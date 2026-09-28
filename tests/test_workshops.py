"""Проверки каталога занятий."""

from datetime import date, timedelta

import pytest

from models.workshops import (
    add_workshop, filter_workshops, find_workshops, sort_workshops,
)


def test_add_workshop_has_unique_id(state):
    workshop = add_workshop(
        state["workshops"], "Акварель", "Иван", date.today(), 500, 1, 0,
    )
    assert workshop.id == 2
    assert len(state["workshops"]) == 2


def test_find_workshops_ignores_case(state):
    assert find_workshops(state["workshops"], " РОСПИСЬ ")[0].id == 1
    assert find_workshops(state["workshops"], "несуществующее") == []


def test_sort_workshops_does_not_modify_original(state):
    add_workshop(state["workshops"], "Лепка", "Иван", date.today(), 500, 1, 0)
    result = sort_workshops(state["workshops"], "price")
    assert [item.id for item in result] == [2, 1]
    assert state["workshops"][0].id == 1
    assert sort_workshops(state["workshops"], "date")[0].id == 2


def test_filter_workshops_by_age_and_date(state):
    assert list(filter_workshops(state["workshops"], [], 11)) == []
    assert len(list(filter_workshops(state["workshops"], [], 12))) == 1
    state["workshops"][0].date = (
        date.today() - timedelta(days=1)
    )
    assert list(filter_workshops(state["workshops"], [], 18)) == []


@pytest.mark.parametrize(
    "capacity, price", [(0, 500), (1, -1), (1, float('nan'))],
)
def test_invalid_workshop_not_added(state, capacity, price):
    with pytest.raises(ValueError):
        add_workshop(
            state["workshops"], "Лепка", "Иван", date.today(),
            price, capacity, 0,
        )
    assert len(state["workshops"]) == 1
