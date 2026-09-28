"""Проверки двух файлов, восстановления связей и защиты данных."""

import json

import pytest

import storage
from models.bookings import create_booking
from storage import load_state, save_state
from models.workshops import available_seats


def test_round_trip_preserves_remaining_seats(tmp_path, state):
    save_state(tmp_path, state, "workshops")
    create_booking(state["workshops"], state["bookings"], 1, "Аня", 18)
    save_state(tmp_path, state, "bookings")
    restored = load_state(tmp_path)
    for key in ("workshops", "bookings"):
        assert [item.to_data() for item in restored[key]] == [
            item.to_data() for item in state[key]
        ]
    assert restored["bookings"][0].workshop is restored["workshops"][0]
    assert available_seats(restored["workshops"][0], restored["bookings"]) == 1


def test_missing_file_starts_empty(tmp_path):
    assert load_state(tmp_path) == {"workshops": [], "bookings": []}


@pytest.mark.parametrize("entity", ["workshops", "bookings"])
@pytest.mark.parametrize("content", ["{broken", "{}", '[1]', '[{}]'])
def test_broken_json_not_overwritten(tmp_path, entity, content):
    filename = tmp_path / f"{entity}.json"
    filename.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        load_state(tmp_path)
    assert filename.read_text(encoding="utf-8") == content


def test_invalid_reference_rejected(tmp_path, state):
    save_state(tmp_path, state, "workshops")
    booking = create_booking(
        state["workshops"], state["bookings"], 1, "Аня", 18,
    ).to_data()
    booking["workshop_id"] = 99
    (tmp_path / "bookings.json").write_text(
        json.dumps([booking]), encoding="utf-8",
    )
    with pytest.raises(ValueError, match="отсутствующее"):
        load_state(tmp_path)


@pytest.mark.parametrize("entity", ["workshops", "bookings"])
def test_failed_replace_keeps_old_file(tmp_path, state, monkeypatch, entity):
    save_state(tmp_path, state, "workshops")
    save_state(tmp_path, state, "bookings")
    original = {file.name: file.read_bytes() for file in tmp_path.iterdir()}

    def fail_replace(source, target):
        raise PermissionError("Нет доступа")

    monkeypatch.setattr(storage.os, "replace", fail_replace)
    if entity == "bookings":
        create_booking(state["workshops"], state["bookings"], 1, "Аня", 18)
    else:
        state["workshops"][0].price = 700
    with pytest.raises(PermissionError):
        save_state(tmp_path, state, entity)
    assert {file.name: file.read_bytes()
            for file in tmp_path.iterdir()} == original


@pytest.mark.parametrize("change", ["duplicate", "capacity", "age"])
def test_inconsistent_state_rejected(tmp_path, state, change):
    create_booking(state["workshops"], state["bookings"], 1, "Аня", 18)
    create_booking(state["workshops"], state["bookings"], 1, "Иван", 18)
    if change == "duplicate":
        state["bookings"][1].id = 1
    elif change == "capacity":
        state["workshops"][0].capacity = 1
    else:
        state["bookings"][0].user.age = 5
    with pytest.raises(ValueError):
        save_state(tmp_path, state, "bookings")


def test_only_selected_entity_is_written(tmp_path, state):
    save_state(tmp_path, state, "workshops")
    workshop_bytes = (tmp_path / "workshops.json").read_bytes()
    create_booking(state["workshops"], state["bookings"], 1, "Аня", 18)
    save_state(tmp_path, state, "bookings")
    assert (tmp_path / "workshops.json").read_bytes() == workshop_bytes
    booking_bytes = (tmp_path / "bookings.json").read_bytes()
    state["workshops"][0].price = 900
    save_state(tmp_path, state, "workshops")
    assert (tmp_path / "bookings.json").read_bytes() == booking_bytes


def test_unsaved_workshop_cannot_be_referenced(tmp_path, state):
    create_booking(state["workshops"], state["bookings"], 1, "Аня", 18)
    with pytest.raises(ValueError, match="Связанные данные"):
        save_state(tmp_path, state, "bookings")
    assert not (tmp_path / "bookings.json").exists()


def test_missing_catalog_with_bookings_is_rejected(tmp_path, state):
    booking = create_booking(
        state["workshops"], state["bookings"], 1, "Аня", 18,
    )
    (tmp_path / "bookings.json").write_text(
        json.dumps([booking.to_data()]), encoding="utf-8",
    )
    with pytest.raises(ValueError, match="отсутствующее"):
        load_state(tmp_path)


def test_duplicate_workshop_ids_rejected(tmp_path, state):
    data = state["workshops"][0].to_data()
    (tmp_path / "workshops.json").write_text(
        json.dumps([data, data]), encoding="utf-8",
    )
    with pytest.raises(ValueError, match="ID занятия"):
        load_state(tmp_path)
