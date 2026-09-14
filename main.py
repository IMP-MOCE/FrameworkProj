"""Начальный сценарий сервиса записи на творческие занятия для ПР1."""

from datetime import date, timedelta


def show_workshop(
    workshop_name, master_name, workshop_date, price,
    available_seats, minimum_age,
):
    """Показать информацию о занятии."""
    print("Сервис записи на творческие занятия")
    print(f"Занятие: {workshop_name}")
    print(f"Мастер: {master_name}")
    print(f"Дата: {workshop_date:%d.%m.%Y}")
    print(f"Стоимость: {price:.2f} руб.")
    print(f"Свободных мест: {available_seats}")
    print(f"Минимальный возраст: {minimum_age} лет")


def check_booking(
    user_name, age_text, minimum_age, available_seats, workshop_date,
):
    """Проверить условия записи и сообщить причину отказа."""
    if not user_name:
        print("Отказ: имя не должно быть пустым.")
        return False
    if (
        not age_text.isascii()
        or not age_text.isdecimal()
        or len(age_text) > 3
    ):
        print("Отказ: возраст должен быть целым числом от 0 до 120.")
        return False

    user_age = int(age_text)
    if user_age > 120:
        print("Отказ: возраст должен быть целым числом от 0 до 120.")
    elif user_age < minimum_age:
        print(f"Отказ: занятие доступно с {minimum_age} лет.")
    elif available_seats <= 0:
        print("Отказ: свободных мест нет.")
    elif workshop_date < date.today():
        print("Отказ: дата занятия уже прошла.")
    else:
        return True
    return False


def create_booking(
    user_name, workshop_name, master_name, workshop_date,
    price, available_seats,
):
    """Подтвердить доступную запись и вернуть статус и остаток мест."""
    print(f"{user_name}, запись доступна. К оплате: {price:.2f} руб.")
    confirmation = input("Подтвердить запись? (да/нет): ").strip().lower()
    if confirmation == "да":
        available_seats -= 1
        print(f"Запись подтверждена: {user_name} — {workshop_name}.")
        print(f"Мастер: {master_name}; дата: {workshop_date:%d.%m.%Y}.")
        print(f"Стоимость: {price:.2f} руб.")
        print(f"Осталось мест: {available_seats}")
        return True, available_seats
    if confirmation == "нет":
        print("Запись отменена пользователем. Число мест не изменилось.")
    else:
        print("Запись не создана: требуется ответ «да» или «нет».")
    return False, available_seats


def main():
    """Выполнить сценарий записи одного пользователя на занятие."""
    workshop_name = "Роспись керамической кружки"
    master_name = "Анна Смирнова"
    workshop_date = date.today() + timedelta(days=7)
    price = 1500.0
    available_seats = 3
    minimum_age = 12
    booking_created = False

    show_workshop(
        workshop_name, master_name, workshop_date, price,
        available_seats, minimum_age,
    )
    user_name = input("Введите имя: ").strip()
    age_text = input("Введите возраст в полных годах (0–120): ").strip()

    can_book = check_booking(
        user_name, age_text, minimum_age, available_seats, workshop_date,
    )
    if can_book:
        booking_created, available_seats = create_booking(
            user_name, workshop_name, master_name, workshop_date,
            price, available_seats,
        )

    print(f"Статус записи: {'создана' if booking_created else 'не создана'}")


if __name__ == "__main__":
    main()
