"""страницы занятий: списки из SQLite, карточка занятия из JSON"""

from datetime import date

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe

from db.database import fetch_all, fetch_one
from models.workshops import find_workshop_by_id
from storage import load_state

# каталог со свободными местами, страница /workshops/
CATALOG_QUERY = """
    SELECT
        workshops.id,
        workshops.name,
        strftime('%d.%m.%Y', workshops.date) AS date_text,
        workshops.price,
        workshops.capacity - COUNT(bookings.id) AS seats
    FROM workshops
    LEFT JOIN bookings
        ON bookings.workshop_id = workshops.id
        AND bookings.status = 'active'
    GROUP BY workshops.id
    ORDER BY workshops.date, workshops.id
"""

# тот же каталог, но только занятия одного мастера
MASTER_CATALOG_QUERY = """
    SELECT
        workshops.id,
        workshops.name,
        strftime('%d.%m.%Y', workshops.date) AS date_text,
        workshops.price,
        workshops.capacity - COUNT(bookings.id) AS seats
    FROM workshops
    LEFT JOIN bookings
        ON bookings.workshop_id = workshops.id
        AND bookings.status = 'active'
    WHERE workshops.master_id = ?
    GROUP BY workshops.id
    ORDER BY workshops.date, workshops.id
"""

# занятия на дату для возраста, у которых остались места
AVAILABLE_QUERY = """
    SELECT
        workshops.id,
        workshops.name,
        strftime('%d.%m.%Y', workshops.date) AS date_text,
        workshops.price,
        workshops.capacity - COUNT(bookings.id) AS seats
    FROM workshops
    LEFT JOIN bookings
        ON bookings.workshop_id = workshops.id
        AND bookings.status = 'active'
    WHERE workshops.date = ?
        AND workshops.minimum_age <= ?
    GROUP BY workshops.id
    HAVING seats > 0
    ORDER BY workshops.name
"""

# мастера с количеством занятий и средней ценой
MASTERS_QUERY = """
    SELECT
        masters.id,
        masters.name,
        COUNT(workshops.id) AS workshops_count,
        AVG(workshops.price) AS average_price
    FROM masters
    LEFT JOIN workshops ON workshops.master_id = masters.id
    GROUP BY masters.id
    ORDER BY masters.name
"""


@require_safe
def workshop_list(request: HttpRequest) -> HttpResponse:
    """каталог занятий, по ссылке со страницы мастеров только его занятия"""
    master = None
    master_id = request.GET.get("master", "")
    if master_id.isdecimal():
        master = fetch_one(
            "SELECT id, name FROM masters WHERE id = ?", [int(master_id)],
        )

    if master is None:
        workshops = fetch_all(CATALOG_QUERY)
    else:
        workshops = fetch_all(MASTER_CATALOG_QUERY, [master["id"]])

    context = {
        "workshops": workshops,
        "master": master,
    }
    return render(request, "workshops/workshop_list.html", context)


def parse_search(date_text: str, age_text: str) -> tuple[date, int] | None:
    """дата и возраст из формы поиска или None, если они неверные"""
    try:
        day = date.fromisoformat(date_text)
        age = int(age_text)
    except ValueError:
        return None
    if not 0 <= age <= 120:
        return None
    return day, age


@require_safe
def available_workshops(request: HttpRequest) -> HttpResponse:
    """поиск занятий со свободными местами на выбранную дату"""
    date_text = request.GET.get("date", "")
    age_text = request.GET.get("age", "")
    searched = bool(date_text or age_text)
    search = parse_search(date_text, age_text)

    workshops = []
    if search is not None:
        day, age = search
        # значения передаются параметрами, а не вставляются в текст запроса
        workshops = fetch_all(AVAILABLE_QUERY, [day.isoformat(), age])

    context = {
        "workshops": workshops,
        "date_text": date_text,
        "age_text": age_text,
        "searched": searched,
        "error": searched and search is None,
    }
    return render(request, "workshops/available.html", context)


@require_safe
def master_list(request: HttpRequest) -> HttpResponse:
    """мастера и сводка по их занятиям"""
    context = {
        "masters": fetch_all(MASTERS_QUERY),
    }
    return render(request, "workshops/master_list.html", context)


@require_safe
def workshop_detail(
    request: HttpRequest, workshop_id: int,
) -> HttpResponse:
    """показать занятие, если его нет, вернуть 404"""
    state = load_state(settings.DATA_DIR)
    workshop = find_workshop_by_id(state["workshops"], workshop_id)

    seats = 0
    available = False
    if workshop is not None:
        seats = workshop.available_seats(state["bookings"])
        available = workshop.date >= date.today() and seats > 0

    context = {
        "workshop": workshop,
        "workshop_id": workshop_id,
        "seats": seats,
        "available": available,
    }
    return render(
        request,
        "workshops/workshop_detail.html",
        context,
        status=404 if workshop is None else 200,
    )
