"""Отображение объектов Booking и связанных занятий и участников."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import escape
from django.views.decorators.http import require_safe

from homepage.views import page
from models.bookings import find_booking_by_id
from storage import load_state


@require_safe
def booking_list(request: HttpRequest) -> HttpResponse:
    """Показать активные и отменённые записи со ссылками на детали."""
    state = load_state(settings.DATA_DIR)
    items = []
    for booking in state["bookings"]:
        url = reverse("bookings:detail", args=[booking.id])
        status = "Активна" if booking.status == "active" else "Отменена"
        badge = "bg-success" if booking.status == "active" else "bg-secondary"
        items.append(f"""
        <li class="list-group-item py-3">
            <a href="{url}">Запись №{booking.id} —
                {escape(booking.workshop.name)}</a>
            <span class="badge {badge}">{status}</span>
            <div class="text-secondary">{escape(booking.user.name)} ·
                {booking.workshop.date:%d.%m.%Y}</div>
        </li>""")
    listing = "".join(items) or '<li class="list-group-item">Записей нет.</li>'
    content = (f'<h1>Записи на занятия</h1>'
               f'<ul class="list-group">{listing}</ul>')
    return HttpResponse(page("Записи", content))


@require_safe
def booking_detail(request: HttpRequest, booking_id: int) -> HttpResponse:
    """Показать запись с данными связанных объектов ПР3."""
    state = load_state(settings.DATA_DIR)
    booking = find_booking_by_id(state["bookings"], booking_id)
    list_url = reverse("bookings:list")
    if booking is None:
        content = f"""
        <h1 class="text-danger">Запись не найдена</h1>
        <a class="btn btn-outline-secondary" href="{list_url}">
            К списку записей</a>
        """
        return HttpResponse(page("Запись не найдена", content), status=404)

    workshop_url = reverse("workshops:detail", args=[booking.workshop.id])
    status = "Активна" if booking.status == "active" else "Отменена"
    badge = "bg-success" if booking.status == "active" else "bg-secondary"
    content = f"""
    <article class="card">
        <div class="card-body p-4">
            <h1>Запись №{booking.id}</h1>
            <p><span class="badge {badge}">{status}</span></p>
            <p>Участник: {escape(booking.user.name)}</p>
            <p>Возраст: {booking.user.age} лет</p>
            <p>Занятие: <a href="{workshop_url}">
                {escape(booking.workshop.name)}</a></p>
            <p>Дата: {booking.workshop.date:%d.%m.%Y}</p>
            <p>Мастер: {escape(booking.workshop.master.name)}</p>
            <a class="btn btn-outline-secondary" href="{list_url}">
                К списку записей</a>
        </div>
    </article>
    """
    return HttpResponse(page(f"Запись №{booking.id}", content))
