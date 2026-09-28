"""Проверки диалога приложения на временных данных."""

from datetime import date, timedelta

import pytest

import main
from storage import load_state, save_state
from workshops import available_seats


def feed(monkeypatch, answers):
    """Подставить ответы вместо ввода с клавиатуры."""
    values = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt: next(values))


def test_all_menu_items(tmp_path, state, monkeypatch, capsys):
    directory = tmp_path
    save_state(directory, state, "workshops")
    day = (date.today() + timedelta(days=10)).strftime("%d.%m.%Y")
    feed(monkeypatch, [
        "ошибка", "11", "1", "2", "РОСПИСЬ", "3", "18", "4", "1",
        "5", "1", "Аня", "18", "6", "1", "Аня", "18", "да", "8",
        "7", "1", "да", "9", "Акварель", "Иван", day, "700", "4", "10",
        "10", "0",
    ])
    main.main(directory)
    output = capsys.readouterr().out
    for text in ("Запись подтверждена", "Место освобождено", "ID: 2",
                 "Активных записей: 0", "Работа завершена"):
        assert text in output
    restored = load_state(directory)
    assert len(restored["workshops"]) == 2
    assert restored["bookings"][0].status == "cancelled"


def test_restart_preserves_booking(tmp_path, state, monkeypatch, capsys):
    directory = tmp_path
    save_state(directory, state, "workshops")
    feed(monkeypatch, ["6", "1", "Аня", "18", "да", "0"])
    main.main(directory)
    capsys.readouterr()
    feed(monkeypatch, ["1", "8", "0"])
    main.main(directory)
    output = capsys.readouterr().out
    assert "Свободных мест: 1" in output
    assert "Аня" in output


def test_failed_save_does_not_change_memory(tmp_path, state, monkeypatch):
    def fail_save(directory, candidate, entity):
        raise PermissionError("Нет доступа")

    monkeypatch.setattr(main, "save_state", fail_save)
    feed(monkeypatch, ["1", "Аня", "18", "да"])
    with pytest.raises(PermissionError):
        main.booking_action(state, tmp_path, create=True)
    assert state["bookings"] == []
    assert available_seats(state["workshops"][0], state["bookings"]) == 2


def test_declining_booking_does_not_save(tmp_path, state, monkeypatch):
    directory = tmp_path
    feed(monkeypatch, ["1", "Аня", "18", "нет"])
    main.booking_action(state, directory, create=True)
    assert not (directory / "bookings.json").exists()
    assert state["bookings"] == []


def test_invalid_input_retried(monkeypatch):
    feed(monkeypatch, ["text", "121", "18"])
    assert main.input_int("Возраст", 0, 120) == 18
    feed(monkeypatch, ["nan", "-1", "100,50"])
    assert main.input_price("Цена") == 100.5
    feed(monkeypatch, ["31.02.2027", "01.01.2000", "01.01.2099"])
    assert main.input_date("Дата") == date(2099, 1, 1)


def test_corrupt_file_stops_without_overwrite(tmp_path, monkeypatch, capsys):
    directory = tmp_path
    catalog = directory / "workshops.json"
    catalog.write_text("broken", encoding="utf-8")
    feed(monkeypatch, [])
    main.main(directory)
    assert "Данные не перезаписаны" in capsys.readouterr().out
    assert catalog.read_text(encoding="utf-8") == "broken"
