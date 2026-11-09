"""главная страница и глобальная страница 404 на шаблонах"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe


@require_safe
def index(request: HttpRequest) -> HttpResponse:
    """показать назначение сервиса и переходы в разделы"""
    return render(request, "homepage/index.html")


def page_not_found(
    request: HttpRequest, exception: Exception,
) -> HttpResponse:
    """обработать неизвестный адрес при DEBUG=False"""
    match = request.resolver_match
    if match is not None and match.url_name == "detail":
        if match.namespace == "workshops":
            return render(request, "workshops/workshop_detail.html", {
                "workshop_id": match.kwargs["workshop_id"],
            }, status=404)
        if match.namespace == "bookings":
            return render(request, "bookings/booking_detail.html", {
                "booking_id": match.kwargs["booking_id"],
            }, status=404)
    return render(request, "homepage/page_not_found.html", status=404)
