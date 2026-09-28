"""Общие проверки значений для классов предметной области."""


def checked_name(value: str) -> str:
    """Проверить имя или название и убрать крайние пробелы."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Имя или название не должно быть пустым.")
    return value.strip()


def checked_int(value: int, minimum: int, maximum: int) -> int:
    """Проверить целое число, исключая логические значения."""
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"Ожидается целое число от {minimum} до {maximum}.")
    return value
