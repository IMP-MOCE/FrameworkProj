"""проверки веб-страниц ПР5-ПР7 на временных JSON и временной базе SQLite"""

import os
from datetime import date, timedelta

import django
import pytest
from django.test import Client, override_settings
from django.urls import Resolver404, resolve, reverse

from db import database
from db.import_json import import_data
from models.bookings import create_booking, find_booking_by_id
from models.workshops import find_workshop_by_id
from storage import save_state

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "creative_studio.settings")
django.setup()


def reimport(directory):
    """перенести изменённый JSON во временную базу"""
    import_data(directory, directory / "studio.sqlite")


@pytest.fixture
def web(tmp_path, state, monkeypatch):
    """Загрузить независимые JSON через те же функции, что и консоль."""
    save_state(tmp_path, state, "workshops")
    create_booking(state["workshops"], state["bookings"], 1, "Мария", 18)
    save_state(tmp_path, state, "bookings")
    reimport(tmp_path)
    # представления читают временную базу, а не data/studio.sqlite
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "studio.sqlite")
    with override_settings(DATA_DIR=tmp_path, DEBUG=False):
        yield Client(HTTP_HOST="localhost"), tmp_path, state


@pytest.mark.parametrize("url, heading", [
    ("/", "Сервис записи на творческие занятия"),
    ("/workshops/", "Творческие занятия"),
    ("/workshops/1/", "Роспись кружки"),
    ("/bookings/", "Записи на занятия"),
    ("/bookings/1/", "Запись №1"),
])
def test_pages_have_shared_html_and_navigation(web, url, heading):
    client, _, _ = web
    response = client.get(url)
    text = response.content.decode()
    assert response.status_code == 200
    assert response["Content-Type"] == "text/html; charset=utf-8"
    assert '<html lang="ru">' in text
    assert '<meta name="viewport"' in text
    assert "bootstrap@5.3.8" in text
    assert heading in text
    for link in ('href="/"', 'href="/workshops/"', 'href="/bookings/"'):
        assert link in text


@pytest.mark.parametrize("url", [
    "/", "/workshops/", "/workshops/1/", "/bookings/", "/bookings/1/",
])
def test_pages_use_base_template_and_static_files(web, url):
    client, _, _ = web
    text = client.get(url).content.decode()
    assert "/static/homepage/css/style.css" in text
    assert "/static/homepage/js/main.js" in text
    assert "/static/homepage/img/logo.svg" in text
    assert 'id="current-year"' in text


def test_lists_show_count_filter(web):
    client, _, _ = web
    assert "Всего занятий: 1" in client.get("/workshops/").content.decode()
    assert "Всего записей: 1" in client.get("/bookings/").content.decode()


def test_page_function_is_removed():
    import homepage.views

    # после ПР6 html собирается только шаблонами
    assert not hasattr(homepage.views, "page")


def test_details_use_domain_objects_and_relations(web):
    client, _, _ = web
    workshop = client.get("/workshops/1/").content.decode()
    booking = client.get("/bookings/1/").content.decode()
    assert "Мастер: Анна" in workshop
    assert "1500.00 руб." in workshop
    assert "Свободных мест: 1" in workshop
    assert "Есть места" in workshop
    assert "Участник: Мария" in booking
    assert "Возраст: 18 лет" in booking
    assert 'href="/workshops/1/"' in booking


def test_named_routes_and_integer_parameters():
    assert reverse("workshops:detail", args=[999]) == "/workshops/999/"
    assert resolve("/workshops/999/").kwargs == {"workshop_id": 999}
    assert reverse("bookings:detail", args=[1]) == "/bookings/1/"
    assert resolve("/bookings/1/").kwargs == {"booking_id": 1}
    with pytest.raises(Resolver404):
        resolve("/workshops/abc/")


@pytest.mark.parametrize("url, message", [
    ("/workshops/999/", "Занятие не найдено"),
    ("/bookings/999/", "Запись не найдена"),
    ("/workshops/abc/", "404 — страница не найдена"),
    ("/unknown/", "404 — страница не найдена"),
])
def test_missing_resource_and_missing_route(web, url, message):
    client, _, _ = web
    response = client.get(url)
    assert response.status_code == 404
    assert message in response.content.decode()


def test_debug_mode_changes_only_global_404(web):
    client, _, _ = web
    with override_settings(DEBUG=True):
        assert "404 — страница не найдена" not in (
            client.get("/unknown/").content.decode()
        )
        assert "Занятие не найдено" in (
            client.get("/workshops/999/").content.decode()
        )


def test_domain_search_returns_object_or_none(web):
    _, _, state = web
    assert find_workshop_by_id(state["workshops"], 1) is state["workshops"][0]
    assert find_booking_by_id(state["bookings"], 1) is state["bookings"][0]
    assert find_workshop_by_id(state["workshops"], 999) is None
    assert find_booking_by_id(state["bookings"], 999) is None


def test_json_change_appears_on_next_request_and_is_escaped(web):
    client, directory, state = web
    state["bookings"].clear()
    save_state(directory, state, "bookings")
    state["workshops"][0].name = '<script>alert("test")</script>'
    save_state(directory, state, "workshops")
    # каталог читает SQLite, поэтому изменения JSON нужно перенести
    reimport(directory)
    for url in ("/workshops/", "/workshops/1/"):
        text = client.get(url).content.decode()
        assert "&lt;script&gt;" in text
        assert '<script>alert("test")</script>' not in text
        assert "Роспись кружки" not in text


def test_empty_json_has_readable_lists(web, tmp_path, monkeypatch):
    client, _, _ = web
    empty = tmp_path / "empty"
    empty.mkdir()
    reimport(empty)
    monkeypatch.setattr(database, "DB_PATH", empty / "studio.sqlite")
    assert "Занятий нет." in client.get("/workshops/").content.decode()
    assert "Записей нет." in client.get("/bookings/").content.decode()
    assert "Мастеров нет." in (
        client.get("/workshops/masters/").content.decode()
    )
    statistics = client.get("/bookings/statistics/").content.decode()
    assert "Всего занятий: 0" in statistics
    assert "Выручка по активным записям: 0.00 руб." in statistics


def test_expired_and_full_workshops_are_unavailable(web):
    client, directory, state = web
    workshop = state["workshops"][0]
    workshop.capacity = 1
    save_state(directory, state, "workshops")
    assert "Запись недоступна" in (
        client.get("/workshops/1/").content.decode()
    )
    workshop.capacity = 2
    workshop.date = date.today() - timedelta(days=1)
    save_state(directory, state, "workshops")
    assert "Запись недоступна" in (
        client.get("/workshops/1/").content.decode()
    )


def test_cancelled_booking_is_shown_and_releases_seat(web):
    client, directory, state = web
    state["bookings"][0].cancel()
    save_state(directory, state, "bookings")
    reimport(directory)
    for url in ("/bookings/", "/bookings/1/"):
        assert "Отменена" in client.get(url).content.decode()
    assert "Свободных мест: 2" in (
        client.get("/workshops/1/").content.decode()
    )


@pytest.mark.parametrize("url", [
    "/", "/workshops/", "/workshops/1/", "/bookings/", "/bookings/1/",
    "/workshops/available/", "/workshops/masters/", "/bookings/statistics/",
])
def test_web_is_read_only_and_supports_head(web, url):
    client, directory, _ = web
    files = [directory / "workshops.json", directory / "bookings.json"]
    before = [file.read_bytes() for file in files]
    assert client.get(url).status_code == 200
    head = client.head(url)
    assert head.status_code == 200
    assert head.content == b""
    post = client.post(url)
    assert post.status_code == 405
    assert post["Allow"] == "GET, HEAD"
    assert [file.read_bytes() for file in files] == before


def test_available_search_uses_date_age_and_free_seats(web):
    client, directory, state = web
    day = state["workshops"][0].date.isoformat()
    url = "/workshops/available/"
    found = client.get(url, {"date": day, "age": 18}).content.decode()
    assert "Найдено занятий: 1" in found
    assert "Свободных мест: 1" in found
    too_young = client.get(url, {"date": day, "age": 10}).content.decode()
    assert "Найдено занятий: 0" in too_young

    # второе место занято: HAVING убирает занятие из результата
    create_booking(state["workshops"], state["bookings"], 1, "Олег", 20)
    save_state(directory, state, "bookings")
    reimport(directory)
    full = client.get(url, {"date": day, "age": 18}).content.decode()
    assert "Найдено занятий: 0" in full


@pytest.mark.parametrize("params", [
    {"date": "2026-13-01", "age": "18"},
    {"date": "2026-10-10", "age": "abc"},
    {"date": "2026-10-10", "age": "121"},
    {"date": "' OR 1=1 --", "age": "18"},
])
def test_available_search_rejects_wrong_input(web, params):
    client, _, _ = web
    response = client.get("/workshops/available/", params)
    assert response.status_code == 200
    assert "Укажите дату и возраст" in response.content.decode()


def test_available_search_without_params_shows_only_form(web):
    client, _, _ = web
    text = client.get("/workshops/available/").content.decode()
    assert '<input type="date"' in text
    assert "Найдено занятий" not in text


def test_masters_page_links_to_filtered_catalog(web):
    client, _, _ = web
    masters = client.get("/workshops/masters/").content.decode()
    assert 'href="/workshops/?master=1"' in masters
    assert "1500.00 руб." in masters
    catalog = client.get("/workshops/", {"master": 1}).content.decode()
    assert "Занятия мастера Анна" in catalog
    assert "Роспись кружки" in catalog
    # неизвестный мастер: показывается весь каталог
    other = client.get("/workshops/", {"master": 999}).content.decode()
    assert "Творческие занятия" in other


def test_statistics_counts_from_database(web):
    client, directory, state = web
    create_booking(state["workshops"], state["bookings"], 1, "Олег", 20)
    state["bookings"][0].cancel()
    save_state(directory, state, "bookings")
    reimport(directory)
    text = client.get("/bookings/statistics/").content.decode()
    assert "Всего занятий: 1" in text
    assert "Активные:" in text and "Отменённые:" in text
    assert "Выручка по активным записям: 1500.00 руб." in text
    assert "Таких занятий пока нет." in text


def test_navigation_has_new_sections(web):
    client, _, _ = web
    text = client.get("/").content.decode()
    assert 'href="/workshops/masters/"' in text
    assert 'href="/bookings/statistics/"' in text
