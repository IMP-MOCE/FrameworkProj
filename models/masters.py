"""Мастер, ведущий творческое занятие."""

from .validation import checked_name


class Master:
    """Ведущий творческого занятия."""

    def __init__(self, name: str) -> None:
        self.name = checked_name(name)

    def __str__(self) -> str:
        return self.name
