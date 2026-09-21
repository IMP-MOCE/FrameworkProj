"""Проверки сохранения и защиты данных от повреждения."""

import json

import pytest

import storage
from bookings import create_booking
from storage import load_state, save_state
from workshops import available_seats


def test_round_trip_preserves_remaining_seats(tmp_path, state):
    create_booking(state["workshops"], state["bookings"], 1, "Аня", 18)
    filename = tmp_path / "state.json"
    save_state(filename, state)
    restored = load_state(filename)
    assert restored == state
    assert available_seats(restored["workshops"][0], restored["bookings"]) == 1


def test_missing_file_starts_empty(tmp_path):
    assert load_state(tmp_path / "missing.json") == {
        "workshops": [], "bookings": [],
    }


@pytest.mark.parametrize("content", ["{broken", "[]", '{"workshops": 1}'])
def test_broken_json_not_overwritten(tmp_path, content):
    filename = tmp_path / "state.json"
    filename.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        load_state(filename)
    assert filename.read_text(encoding="utf-8") == content


def test_invalid_reference_rejected(tmp_path, state):
    create_booking(state["workshops"], state["bookings"], 1, "Аня", 18)
    state["bookings"][0]["workshop_id"] = 99
    filename = tmp_path / "state.json"
    filename.write_text(json.dumps(state), encoding="utf-8")
    with pytest.raises(ValueError, match="отсутствующее"):
        load_state(filename)


def test_failed_replace_keeps_old_file(tmp_path, state, monkeypatch):
    filename = tmp_path / "state.json"
    save_state(filename, state)
    original = filename.read_bytes()

    def fail_replace(source, target):
        raise PermissionError("Нет доступа")

    monkeypatch.setattr(storage.os, "replace", fail_replace)
    create_booking(state["workshops"], state["bookings"], 1, "Аня", 18)
    with pytest.raises(PermissionError):
        save_state(filename, state)
    assert filename.read_bytes() == original


@pytest.mark.parametrize("change", ["duplicate", "capacity", "age"])
def test_inconsistent_state_rejected(tmp_path, state, change):
    create_booking(state["workshops"], state["bookings"], 1, "Аня", 18)
    create_booking(state["workshops"], state["bookings"], 1, "Иван", 18)
    if change == "duplicate":
        state["bookings"][1]["id"] = 1
    elif change == "capacity":
        state["workshops"][0]["capacity"] = 1
    else:
        state["bookings"][0]["user_age"] = 5
    with pytest.raises(ValueError):
        save_state(tmp_path / "state.json", state)
