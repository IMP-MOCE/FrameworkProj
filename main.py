"""Начальный сценарий сервиса записи на творческие занятия для ПР1."""

from datetime import date, timedelta


# Демонстрационные данные одного занятия и одного пользователя.
workshop_name = "Роспись керамической кружки"
master_name = "Анна Смирнова"
workshop_date = date.today() + timedelta(days=7)
price = 1500.0
available_seats = 3
minimum_age = 12
booking_created = False

print("Сервис записи на творческие занятия")
print(f"Занятие: {workshop_name}")
print(f"Мастер: {master_name}")
print(f"Дата: {workshop_date:%d.%m.%Y}")
print(f"Стоимость: {price:.2f} руб.")
print(f"Свободных мест: {available_seats}")
print(f"Минимальный возраст: {minimum_age} лет")

user_name = input("Введите имя: ").strip()
age_text = input("Введите возраст в полных годах (0–120): ").strip()

if not user_name:
    print("Отказ: имя не должно быть пустым.")
elif not age_text.isascii() or not age_text.isdecimal():
    print("Отказ: возраст должен быть целым числом от 0 до 120.")
elif len(age_text) > 3:
    print("Отказ: возраст должен быть целым числом от 0 до 120.")
else:
    user_age = int(age_text)
    can_book = (
        user_age <= 120
        and user_age >= minimum_age
        and available_seats > 0
        and workshop_date >= date.today()
    )

    if user_age > 120:
        print("Отказ: возраст должен быть целым числом от 0 до 120.")
    elif user_age < minimum_age:
        print(f"Отказ: занятие доступно с {minimum_age} лет.")
    elif available_seats <= 0:
        print("Отказ: свободных мест нет.")
    elif workshop_date < date.today():
        print("Отказ: дата занятия уже прошла.")
    elif can_book:
        print(f"{user_name}, запись доступна. К оплате: {price:.2f} руб.")
        confirmation = input("Подтвердить запись? (да/нет): ").strip().lower()
        if confirmation == "да":
            booking_created = True
            available_seats -= 1
            print(f"Запись подтверждена: {user_name} — {workshop_name}.")
            print(f"Мастер: {master_name}; дата: {workshop_date:%d.%m.%Y}.")
            print(f"Стоимость: {price:.2f} руб.")
            print(f"Осталось мест: {available_seats}")
        elif confirmation == "нет":
            print("Запись отменена пользователем. Число мест не изменилось.")
        else:
            print("Запись не создана: требуется ответ «да» или «нет».")

print(f"Статус записи: {'создана' if booking_created else 'не создана'}")
