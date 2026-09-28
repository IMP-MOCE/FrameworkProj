"""Консольный сервис записи на творческие занятия, ПР3."""

from collections.abc import Iterable
from copy import deepcopy
from pathlib import Path

from bookings import cancel_booking, check_booking, create_booking
from models import Booking, Workshop
from storage import State, load_state, save_state
from utils import confirm, input_date, input_int, input_price, input_text
from workshops import (
    add_workshop, available_seats, filter_workshops, find_workshops,
    get_workshop, sort_workshops,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
MENU = """
=== Сервис записи на творческие занятия ===
1. Показать занятия
2. Найти занятие по названию
3. Показать доступные занятия для моего возраста
4. Сортировать занятия
5. Проверить возможность записи
6. Записаться на занятие
7. Отменить запись
8. Показать записи
9. Добавить занятие
10. Статистика
0. Выход
"""


def show_workshop(workshop: Workshop, bookings: list[Booking]) -> None:
    """Показать занятие и актуальный остаток мест (сценарий ПР1)."""
    day = workshop.date
    print(f"[{workshop.id}] {workshop.name}")
    print(f"Мастер: {workshop.master}; дата: {day:%d.%m.%Y}")
    print(f"Стоимость: {workshop.price:.2f} руб.")
    print(f"Свободных мест: {available_seats(workshop, bookings)}")
    print(f"Минимальный возраст: {workshop.minimum_age} лет")


def show_workshops(items: Iterable[Workshop], bookings: list[Booking]) -> None:
    """Вывести список или генератор занятий."""
    found = False
    for workshop in items:
        show_workshop(workshop, bookings)
        print()
        found = True
    if not found:
        print("Подходящих занятий нет.")


def show_bookings(state: State) -> None:
    """Показать активные и отменённые записи с именами участников."""
    if not state["bookings"]:
        print("Записей пока нет.")
    for booking in state["bookings"]:
        print(booking)


def select_workshop(state: State) -> Workshop:
    """Получить ID и проверить существование занятия."""
    workshop_id = input_int("ID занятия: ", 1, 1_000_000_000)
    return get_workshop(state["workshops"], workshop_id)


def booking_action(state: State, directory: Path, create: bool) -> None:
    """Проверить условия и при подтверждении сохранить новую запись."""
    workshop = select_workshop(state)
    show_workshop(workshop, state["bookings"])
    user_name = input_text("Введите имя: ")
    user_age = input_int("Введите возраст (0–120): ", 0, 120)
    reason = check_booking(workshop, state["bookings"], user_name, user_age)
    if reason:
        print(f"Отказ: {reason}")
        return
    print(f"Запись доступна. К оплате: {workshop.price:.2f} руб.")
    if not create:
        return
    if not confirm("Подтвердить запись? (да/нет): "):
        print("Запись не создана. Число мест не изменилось.")
        return
    candidate = deepcopy(state)
    booking = create_booking(
        candidate["workshops"], candidate["bookings"], workshop.id,
        user_name, user_age,
    )
    save_state(directory, candidate, "bookings")
    state.update(candidate)
    print(f"Запись подтверждена. Номер записи: {booking.id}.")
    print(f"Осталось мест: {available_seats(workshop, state['bookings'])}")


def cancellation_action(state: State, directory: Path) -> None:
    """Отменить запись после подтверждения и успешного сохранения."""
    booking_id = input_int("Номер записи: ", 1, 1_000_000_000)
    candidate = deepcopy(state)
    booking = cancel_booking(candidate["bookings"], booking_id)
    print(f"Участник: {booking.user.name}")
    if not confirm("Отменить запись? (да/нет): "):
        print("Отмена не выполнена.")
        return
    save_state(directory, candidate, "bookings")
    state.update(candidate)
    print("Запись отменена. Место освобождено.")


def addition_action(state: State, directory: Path) -> None:
    """Ввести данные и сохранить новое занятие."""
    name = input_text("Название занятия: ")
    master = input_text("Имя мастера: ")
    day = input_date("Дата (ДД.ММ.ГГГГ): ")
    price = input_price("Стоимость в рублях: ")
    capacity = input_int("Количество мест: ", 1, 10000)
    minimum_age = input_int("Минимальный возраст: ", 0, 120)
    candidate = deepcopy(state)
    workshop = add_workshop(
        candidate["workshops"], name, master, day, price, capacity,
        minimum_age,
    )
    save_state(directory, candidate, "workshops")
    state.update(candidate)
    print(f"Занятие добавлено. ID: {workshop.id}.")


def show_statistics(state: State) -> None:
    """Вывести число занятий, мастеров и записей по статусам."""
    masters = {item.master.name.casefold() for item in state["workshops"]}
    active = sum(item.status == "active" for item in state["bookings"])
    print(f"Занятий: {len(state['workshops'])}; мастеров: {len(masters)}")
    print(f"Активных записей: {active}")
    print(f"Отменённых записей: {len(state['bookings']) - active}")


def main(directory: Path = DATA_DIR) -> None:
    """Загрузить данные и повторять меню до команды выхода."""
    try:
        if not any((directory / name).exists() for name in
                   ("workshops.json", "bookings.json")):
            print("Файлы данных отсутствуют. Открыт пустой каталог.")
        state = load_state(directory)
    except (OSError, ValueError) as error:
        print(f"Не удалось загрузить данные: {error}")
        print("Исправьте файл и повторите запуск. Данные не перезаписаны.")
        return
    while True:
        try:
            print(MENU)
            choice = input_int("Выберите действие: ", 0, 10)
            if choice == 0:
                print("Работа завершена.")
                break
            if choice == 1:
                show_workshops(state["workshops"], state["bookings"])
            elif choice == 2:
                query = input_text("Часть названия: ")
                show_workshops(
                    find_workshops(state["workshops"], query),
                    state["bookings"],
                )
            elif choice == 3:
                age = input_int("Возраст: ", 0, 120)
                show_workshops(
                    filter_workshops(state["workshops"], state["bookings"],
                                     age), state["bookings"],
                )
            elif choice == 4:
                order = input_int("1 — по цене, 2 — по дате: ", 1, 2)
                key = "price" if order == 1 else "date"
                show_workshops(
                    sort_workshops(state["workshops"], key), state["bookings"],
                )
            elif choice == 5:
                booking_action(state, directory, create=False)
            elif choice == 6:
                booking_action(state, directory, create=True)
            elif choice == 7:
                cancellation_action(state, directory)
            elif choice == 8:
                show_bookings(state)
            elif choice == 9:
                addition_action(state, directory)
            elif choice == 10:
                show_statistics(state)
        except ValueError as error:
            print(f"Ошибка: {error}")
        except OSError as error:
            print(f"Не удалось сохранить изменения: {error}")
            print("Изменения не применены. Проверьте доступ к файлу.")
        except (EOFError, KeyboardInterrupt):
            print("\nРабота завершена. Подтверждённые изменения сохранены.")
            break


if __name__ == "__main__":
    main()
