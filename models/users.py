"""Участник творческого занятия."""

from .validation import checked_int, checked_name


class User:
    """Участник, определяемый именем и возрастом."""

    def __init__(self, name: str, age: int) -> None:
        self.name = checked_name(name)
        self.age = checked_int(age, 0, 120)

    def identity(self) -> tuple[str, int]:
        """Получить ключ участника для проверки повторной записи."""
        return self.name.strip().casefold(), self.age

    def __str__(self) -> str:
        return f"{self.name}, {self.age} лет"
