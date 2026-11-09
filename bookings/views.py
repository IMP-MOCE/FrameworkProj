"""Записи, фильтрация, пагинация и статистика средствами ORM."""

from datetime import date
from re import escape

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Max, Min, Q, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_safe

from users.models import User
from workshops.models import Workshop
from .models import Booking

POPULAR_MIN_BOOKINGS = 2
SORTS = {
    "date": ("workshop__date", "pk"),
    "-date": ("-workshop__date", "pk"),
    "workshop": ("workshop__name", "pk"),
    "user": ("user__name", "pk"),
}


@require_safe
def booking_list(request: HttpRequest) -> HttpResponse:
    bookings = Booking.objects.all()
    errors = []
    for parameter in ("workshop", "user"):
        value = request.GET.get(parameter, "")
        if value:
            if value.isdecimal() and len(value) < 19 and int(value) > 0:
                bookings = bookings.filter(**{f"{parameter}_id": int(value)})
            else:
                errors.append(
                    "Укажите корректный номер занятия или участника.",
                )
    date_text = request.GET.get("date", "")
    if date_text:
        try:
            day = date.fromisoformat(date_text)
        except ValueError:
            errors.append("Укажите корректную дату.")
        else:
            bookings = bookings.filter(workshop__date=day)
    status = request.GET.get("status", "")
    if status == "active":
        bookings = bookings.exclude(status=Booking.Status.CANCELLED)
    elif status == "cancelled":
        bookings = bookings.filter(status=Booking.Status.CANCELLED)
    elif status:
        errors.append("Выберите корректный статус.")
    query = request.GET.get("q", "").strip()
    if query:
        bookings = bookings.filter(
            Q(workshop__name__iregex=escape(query))
            | Q(user__name__iregex=escape(query)),
        )
    if errors:
        bookings = bookings.none()
    sort = request.GET.get("sort", "date")
    if sort not in SORTS:
        sort = "date"
    # values возвращает словари, F задаёт понятные шаблону имена полей.
    rows = bookings.order_by(*SORTS[sort]).annotate(
        workshop_name=F("workshop__name"), user_name=F("user__name"),
        workshop_date=F("workshop__date"),
    ).values("id", "status", "workshop_name", "user_name", "workshop_date")
    page_obj = Paginator(rows, settings.BOOKINGS_PAGE_SIZE).get_page(
        request.GET.get("page"),
    )
    return render(request, "bookings/booking_list.html", {
        "bookings": page_obj, "page_obj": page_obj, "errors": errors,
        "workshops": Workshop.objects.all(), "users": User.objects.all(),
        "filters": request.GET, "sort": sort, "query": query,
    })


@require_safe
def statistics(request: HttpRequest) -> HttpResponse:
    catalog = Workshop.objects.aggregate(
        workshops_count=Count("pk"), min_price=Min("price"),
        max_price=Max("price"), average_price=Avg("price"),
    )
    statuses = Booking.objects.order_by("status").values("status").annotate(
        bookings_count=Count("pk"),
    )
    revenue = Booking.objects.exclude(status="cancelled").aggregate(
        total=Sum("workshop__price"),
    )
    users = User.objects.annotate(
        active_count=Count(
            "bookings", filter=Q(bookings__status="active"),
        ),
    ).order_by("-active_count", "name", "pk")
    popular = Workshop.objects.with_seats().filter(
        active_count__gte=POPULAR_MIN_BOOKINGS,
    ).order_by("-active_count", "name", "pk")
    return render(request, "bookings/statistics.html", {
        "catalog": catalog, "statuses": statuses, "revenue": revenue,
        "users": users, "popular": popular,
        "popular_min": POPULAR_MIN_BOOKINGS,
    })


@require_safe
def booking_detail(request: HttpRequest, booking_id: int) -> HttpResponse:
    booking = get_object_or_404(
        Booking.objects.select_related("workshop__master", "user"),
        pk=booking_id,
    )
    return render(request, "bookings/booking_detail.html", {
        "booking": booking,
    })
