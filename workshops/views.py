"""Отображение объектов Workshop из JSON-хранилища ПР3."""

from datetime import date

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import escape
from django.views.decorators.http import require_safe

from homepage.views import page
from models.workshops import find_workshop_by_id
from storage import load_state


@require_safe
def workshop_list(request: HttpRequest) -> HttpResponse:
    """Загрузить занятия и показать ссылки на их карточки."""
    state = load_state(settings.DATA_DIR)
    items = []
    for workshop in state["workshops"]:
        url = reverse("workshops:detail", args=[workshop.id])
        seats = workshop.available_seats(state["bookings"])
        items.append(f"""
        <li class="list-group-item py-3">
            <a href="{url}">{escape(workshop.name)}</a>
            <div class="text-secondary">
                {workshop.date:%d.%m.%Y} · {workshop.price:.2f} руб.
                · Свободных мест: {seats}
            </div>
        </li>""")
    listing = "".join(items) or '<li class="list-group-item">Занятий нет.</li>'
    content = f"""
    <h1>Творческие занятия</h1>
    <p>Откройте занятие, чтобы посмотреть мастера и условия участия.</p>
    <ul class="list-group">{listing}</ul>
    """
    return HttpResponse(page("Занятия", content))


@require_safe
def workshop_detail(
    request: HttpRequest, workshop_id: int,
) -> HttpResponse:
    """Найти объект занятия; отсутствующий ID вернуть как HTTP 404."""
    state = load_state(settings.DATA_DIR)
    workshop = find_workshop_by_id(state["workshops"], workshop_id)
    list_url = reverse("workshops:list")
    if workshop is None:
        content = f"""
        <h1 class="text-danger">Занятие не найдено</h1>
        <p>Занятия с номером {workshop_id} нет в каталоге.</p>
        <a href="{list_url}" class="btn btn-outline-secondary">
            К списку занятий</a>
        """
        return HttpResponse(page("Занятие не найдено", content), status=404)

    seats = workshop.available_seats(state["bookings"])
    available = workshop.date >= date.today() and seats > 0
    status = "Есть места" if available else "Запись недоступна"
    badge = "bg-success" if available else "bg-secondary"
    content = f"""
    <article class="card">
        <div class="card-body p-4">
            <h1>{escape(workshop.name)}</h1>
            <p><span class="badge {badge}">{status}</span></p>
            <p>ID: {workshop.id}</p>
            <p>Мастер: {escape(workshop.master.name)}</p>
            <p>Дата: {workshop.date:%d.%m.%Y}</p>
            <p>Стоимость: {workshop.price:.2f} руб.</p>
            <p>Вместимость: {workshop.capacity} мест</p>
            <p>Свободных мест: {seats}</p>
            <p>Минимальный возраст: {workshop.minimum_age} лет</p>
            <a href="{list_url}" class="btn btn-outline-secondary">
                К списку занятий</a>
        </div>
    </article>
    """
    return HttpResponse(page(workshop.name, content))
