"""страницы записей: данные из JSON, HTML из шаблонов"""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe

from models.bookings import find_booking_by_id
from storage import load_state


@require_safe
def booking_list(request: HttpRequest) -> HttpResponse:
    """передать в шаблон активные и отменённые записи"""
    state = load_state(settings.DATA_DIR)
    context = {
        "bookings": state["bookings"],
    }
    return render(request, "bookings/booking_list.html", context)


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
