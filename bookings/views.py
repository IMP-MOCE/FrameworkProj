"""страницы записей: список и статистика из SQLite, запись из JSON"""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe

from db.database import fetch_all, fetch_one
from models.bookings import find_booking_by_id
from storage import load_state

# все записи с названием занятия и именем участника из трёх таблиц
BOOKINGS_QUERY = """
    SELECT
        bookings.id,
        bookings.status,
        workshops.name AS workshop_name,
        strftime('%d.%m.%Y', workshops.date) AS workshop_date,
        users.name AS user_name
    FROM bookings
    JOIN workshops ON bookings.workshop_id = workshops.id
    JOIN users ON bookings.user_id = users.id
    ORDER BY bookings.id
"""

CATALOG_SUMMARY_QUERY = """
    SELECT
        COUNT(*) AS workshops_count,
        MIN(price) AS min_price,
        MAX(price) AS max_price,
        AVG(price) AS average_price
    FROM workshops
"""

STATUS_QUERY = """
    SELECT status, COUNT(*) AS bookings_count
    FROM bookings
    GROUP BY status
    ORDER BY status
"""

REVENUE_QUERY = """
    SELECT SUM(workshops.price) AS total
    FROM bookings
    JOIN workshops ON bookings.workshop_id = workshops.id
    WHERE bookings.status = 'active'
"""

USERS_QUERY = """
    SELECT
        users.name,
        users.age,
        COUNT(bookings.id) AS active_count
    FROM users
    LEFT JOIN bookings
        ON bookings.user_id = users.id
        AND bookings.status = 'active'
    GROUP BY users.id
    ORDER BY active_count DESC, users.name
"""

# занятия, у которых активных записей не меньше заданного числа
POPULAR_QUERY = """
    SELECT
        workshops.name,
        COUNT(bookings.id) AS active_count
    FROM workshops
    JOIN bookings ON bookings.workshop_id = workshops.id
    WHERE bookings.status = 'active'
    GROUP BY workshops.id
    HAVING COUNT(bookings.id) >= ?
    ORDER BY active_count DESC
"""

POPULAR_MIN_BOOKINGS = 2


@require_safe
def booking_list(request: HttpRequest) -> HttpResponse:
    """передать в шаблон активные и отменённые записи"""
    context = {
        "bookings": fetch_all(BOOKINGS_QUERY),
    }
    return render(request, "bookings/booking_list.html", context)


@require_safe
def statistics(request: HttpRequest) -> HttpResponse:
    """сводка по каталогу, записям и участникам"""
    context = {
        "catalog": fetch_one(CATALOG_SUMMARY_QUERY),
        "statuses": fetch_all(STATUS_QUERY),
        "revenue": fetch_one(REVENUE_QUERY),
        "users": fetch_all(USERS_QUERY),
        "popular": fetch_all(POPULAR_QUERY, [POPULAR_MIN_BOOKINGS]),
        "popular_min": POPULAR_MIN_BOOKINGS,
    }
    return render(request, "bookings/statistics.html", context)


@require_safe
def booking_detail(request: HttpRequest, booking_id: int) -> HttpResponse:
    """показать запись, если её нет, вернуть 404"""
    state = load_state(settings.DATA_DIR)
    booking = find_booking_by_id(state["bookings"], booking_id)
    context = {
        "booking": booking,
        "booking_id": booking_id,
    }
    return render(
        request,
        "bookings/booking_detail.html",
        context,
        status=404 if booking is None else 200,
    )
