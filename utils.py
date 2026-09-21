"""Ввод пользовательских данных с повторным запросом при ошибке."""

from datetime import date, datetime
from math import isfinite


def input_text(prompt: str) -> str:
    """Запрашивать непустую строку и удалить крайние пробелы."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Значение не должно быть пустым.")


def input_int(prompt: str, minimum: int, maximum: int) -> int:
    """Запрашивать целое число из заданного диапазона."""
    while True:
        try:
            value = int(input(prompt))
            if not minimum <= value <= maximum:
                raise ValueError
            return value
        except ValueError:
            print(f"Введите целое число от {minimum} до {maximum}.")


def input_date(prompt: str) -> date:
    """Запрашивать существующую дату не раньше сегодняшней."""
    while True:
        try:
            value = datetime.strptime(input(prompt).strip(), "%d.%m.%Y")
            if value.date() < date.today():
                raise ValueError
            return value.date()
        except ValueError:
            print("Введите дату ДД.ММ.ГГГГ, не раньше сегодняшней.")


def input_price(prompt: str) -> float:
    """Запрашивать неотрицательную конечную цену в рублях."""
    while True:
        try:
            value = float(input(prompt).strip().replace(",", "."))
            if not isfinite(value) or not 0 <= value <= 1_000_000:
                raise ValueError
            return round(value, 2)
        except ValueError:
            print("Введите цену от 0 до 1000000 рублей.")


def confirm(prompt: str) -> bool:
    """Получить ответ да или нет, повторяя запрос при другом вводе."""
    while True:
        answer = input(prompt).strip().casefold()
        if answer in ("да", "нет"):
            return answer == "да"
        print("Введите «да» или «нет».")
