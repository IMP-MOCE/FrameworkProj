"""Проверки веб-страниц ПР5 без БД и без изменения рабочего JSON."""

import os
from datetime import date, timedelta

import django
import pytest
from django.test import Client, override_settings
from django.urls import Resolver404, resolve, reverse

from models.bookings import create_booking, find_booking_by_id
from models.workshops import find_workshop_by_id
from storage import save_state

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "creative_studio.settings")
django.setup()


@pytest.fixture
def web(tmp_path, state):
    """Загрузить независимые JSON через те же функции, что и консоль."""
    save_state(tmp_path, state, "workshops")
    create_booking(state["workshops"], state["bookings"], 1, "Мария", 18)
    save_state(tmp_path, state, "bookings")
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
    for url in ("/workshops/", "/workshops/1/"):
        text = client.get(url).content.decode()
        assert "&lt;script&gt;" in text
        assert '<script>alert("test")</script>' not in text
        assert "Роспись кружки" not in text


def test_empty_json_has_readable_lists(web, tmp_path):
    client, _, _ = web
    with override_settings(DATA_DIR=tmp_path / "empty"):
        assert "Занятий нет." in client.get("/workshops/").content.decode()
        assert "Записей нет." in client.get("/bookings/").content.decode()


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
    for url in ("/bookings/", "/bookings/1/"):
        assert "Отменена" in client.get(url).content.decode()
    assert "Свободных мест: 2" in (
        client.get("/workshops/1/").content.decode()
    )


@pytest.mark.parametrize("url", [
    "/", "/workshops/", "/workshops/1/", "/bookings/", "/bookings/1/",
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
