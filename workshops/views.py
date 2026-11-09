"""Каталог, карточки и поиск занятий через Django ORM."""

from datetime import date
from re import escape

from django.db.models import Avg, Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_safe

from masters.models import Master
from .models import Workshop


@require_safe
def workshop_list(request: HttpRequest) -> HttpResponse:
    workshops = Workshop.objects.with_seats().select_related("master")
    master = None
    master_id = request.GET.get("master", "")
    if master_id.isdecimal() and len(master_id) < 19:
        master = Master.objects.filter(pk=int(master_id)).first()
        if master is not None:
            workshops = workshops.filter(master=master)
    query = request.GET.get("q", "").strip()
    if query:
        workshops = workshops.filter(name__iregex=escape(query))
    sort = request.GET.get("sort", "date")
    sorts = {"date": ("date", "pk"), "price": ("price", "pk"),
             "name": ("name", "pk"), "-price": ("-price", "pk")}
    if sort not in sorts:
        sort = "date"
    return render(request, "workshops/workshop_list.html", {
        "workshops": workshops.order_by(*sorts[sort]),
        "master": master, "query": query, "sort": sort,
    })


def parse_search(date_text: str, age_text: str) -> tuple[date, int] | None:
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
    date_text = request.GET.get("date", "")
    age_text = request.GET.get("age", "")
    searched = bool(date_text or age_text)
    search = parse_search(date_text, age_text)
    workshops = Workshop.objects.none()
    if search is not None:
        day, age = search
        workshops = Workshop.objects.with_seats().filter(
            date=day, minimum_age__lte=age, seats__gt=0,
        ).order_by("name", "pk")
    return render(request, "workshops/available.html", {
        "workshops": workshops, "date_text": date_text, "age_text": age_text,
        "searched": searched, "error": searched and search is None,
    })


@require_safe
def master_list(request: HttpRequest) -> HttpResponse:
    masters = Master.objects.annotate(
        workshops_count=Count("workshops"),
        average_price=Avg("workshops__price"),
    ).order_by("name", "pk")
    return render(request, "workshops/master_list.html", {"masters": masters})


@require_safe
def workshop_detail(request: HttpRequest, workshop_id: int) -> HttpResponse:
    workshop = get_object_or_404(
        Workshop.objects.with_seats().select_related("master"), pk=workshop_id,
    )
    return render(request, "workshops/workshop_detail.html", {
        "workshop": workshop, "seats": workshop.seats,
        "available": workshop.date >= date.today() and workshop.seats > 0,
    })
