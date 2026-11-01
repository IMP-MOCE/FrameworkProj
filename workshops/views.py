"""страницы занятий: данные из JSON, HTML из шаблонов"""

from datetime import date

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe

from models.workshops import find_workshop_by_id
from storage import load_state


@require_safe
def workshop_list(request: HttpRequest) -> HttpResponse:
    """передать в шаблон занятия вместе с числом свободных мест"""
    state = load_state(settings.DATA_DIR)
    workshops = []
    for workshop in state["workshops"]:
        seats = workshop.available_seats(state["bookings"])
        workshops.append((workshop, seats))

    context = {
        "workshops": workshops,
    }
    return render(request, "workshops/workshop_list.html", context)


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
