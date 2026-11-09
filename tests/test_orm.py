"""ПР9: перенос, CRUD, ограничения, запросы и навигация."""

from datetime import date, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.db import connection

from bookings.models import Booking
from bookings.services import create_booking
from db.import_json import import_data as import_sqlite
from db.import_sqlite_to_orm import import_data
from masters.models import Master
from storage import save_state
from users.models import User
from workshops.models import Workshop

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalog():
    master = Master.objects.create(name="Анна")
    workshop = Workshop.objects.create(
        name="Роспись кружки", master=master,
        date=date.today() + timedelta(days=7), price=1500,
        capacity=2, minimum_age=12,
    )
    user = User.objects.create(name="Мария", age=18)
    return workshop, user


@pytest.fixture
def client():
    with override_settings(DEBUG=False):
        yield Client(HTTP_HOST="localhost")


def test_crud_relations_cancel_and_delete(catalog):
    workshop, user = catalog
    booking = create_booking(workshop.pk, user)
    assert list(workshop.bookings.all()) == [booking]
    assert user.bookings.get().workshop == workshop
    user.name = "Ирина"
    user.full_clean()
    user.save()
    user.refresh_from_db()
    assert user.name == "Ирина"
    with pytest.raises(ProtectedError):
        workshop.delete()
    booking.cancel()
    assert Workshop.objects.with_seats().get().seats == 2
    booking.delete()
    assert not Booking.objects.exists()


def test_creation_rules_capacity_age_duplicates_and_date(catalog):
    workshop, user = catalog
    young = User.objects.create(name="Младший", age=10)
    with pytest.raises(ValidationError):
        create_booking(workshop.pk, young)
    create_booking(workshop.pk, user)
    with pytest.raises(ValidationError):
        create_booking(workshop.pk, user)
    twin = User.objects.create(name="МАРИЯ", age=18)
    with pytest.raises(ValidationError):
        create_booking(workshop.pk, twin)
    other = User.objects.create(name="Другой", age=20)
    create_booking(workshop.pk, other)
    with pytest.raises(ValidationError):
        create_booking(workshop.pk, twin)
    workshop.date = date.today() - timedelta(days=1)
    workshop.save()
    with pytest.raises(ValidationError, match="прошла"):
        create_booking(workshop.pk, twin)


def test_import_repeated_and_conflict_rolls_back(tmp_path, state):
    save_state(tmp_path, state, "workshops")
    source = tmp_path / "source.sqlite"
    import_sqlite(tmp_path, source)
    before = source.read_bytes()
    counts = import_data(source)
    assert counts["workshops"] == 1
    assert import_data(source) == counts
    workshop = Workshop.objects.get(pk=1)
    assert workshop.master.name == "Анна"
    workshop.name = "Изменено через ORM"
    workshop.save()
    Master.objects.all().update(name="Изменённый мастер")
    with pytest.raises(ValueError, match="Конфликт"):
        import_data(source)
    assert Workshop.objects.get(pk=1).name == "Изменено через ORM"
    assert Master.objects.get().name == "Изменённый мастер"
    assert source.read_bytes() == before


def test_failed_import_is_atomic(tmp_path, state):
    save_state(tmp_path, state, "workshops")
    source = tmp_path / "source.sqlite"
    import_sqlite(tmp_path, source)
    # Ошибка в последней сущности после успешного создания мастера и занятия.
    import sqlite3
    with sqlite3.connect(source) as conn:
        conn.execute("INSERT INTO users VALUES (1, 'Малыш', 1)")
        conn.execute("INSERT INTO bookings VALUES (1, 1, 1, 'active')")
    with pytest.raises(ValidationError):
        import_data(source)
    assert not Master.objects.exists()
    assert not Workshop.objects.exists()
    assert not User.objects.exists()


@pytest.mark.parametrize("params", [
    {"date": "wrong"}, {"user": "abc"}, {"workshop": "-1"},
    {"user": "9" * 5000}, {"status": "invalid"},
])
def test_invalid_filters_are_visible_errors(client, params):
    response = client.get("/bookings/", params)
    assert response.status_code == 200
    assert response.context["errors"]
    assert response.context["page_obj"].paginator.count == 0


def test_filters_search_sort_pagination_keep_parameters(client, catalog):
    workshop, user = catalog
    create_booking(workshop.pk, user)
    other = User.objects.create(name="Ольга", age=22)
    create_booking(workshop.pk, other)
    params = {"q": "РОСПИСЬ", "status": "active", "sort": "user"}
    with override_settings(BOOKINGS_PAGE_SIZE=1):
        response = client.get("/bookings/", params)
        page = response.context["page_obj"]
        assert page.paginator.count == 2
        assert page.number == 1
        assert list(page)[0]["user_name"] == "Мария"
        from html.parser import HTMLParser

        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.urls = []

            def handle_starttag(self, tag, attrs):
                self.urls += [
                    v for k, v in attrs if tag == "a" and k == "href"
                ]

        links = Links()
        links.feed(response.content.decode())
        next_link = next(url for url in links.urls if "page=2" in url)
        query = parse_qs(urlsplit(next_link).query)
        assert query == {**{k: [v] for k, v in params.items()}, "page": ["2"]}
        second = client.get("/bookings/" + next_link)
        assert second.context["page_obj"].number == 2
        assert list(second.context["page_obj"])[0]["user_name"] == "Ольга"
        for page_input, expected in [("bad", 1), ("999", 2), ("-1", 2)]:
            result = client.get("/bookings/", {**params, "page": page_input})
            assert result.context["page_obj"].number == expected
    for key, value in [("user", user.pk), ("workshop", workshop.pk),
                       ("date", workshop.date.isoformat()), ("q", "мария")]:
        response = client.get("/bookings/", {key: value})
        assert response.context["page_obj"].paginator.count >= 1
    assert client.get("/bookings/", {"status": "cancelled"}).context[
        "page_obj"
    ].paginator.count == 0


def test_orm_change_updates_card_and_catalog(client, catalog):
    workshop, _ = catalog
    workshop.name = "Новое название"
    workshop.save()
    for url in ("/workshops/", f"/workshops/{workshop.pk}/"):
        assert "Новое название" in client.get(url).content.decode()
    result = client.get("/workshops/", {"q": "НОВОЕ", "sort": "bad"})
    assert result.context["sort"] == "date"
    assert len(result.context["workshops"]) == 1


def test_detail_fetches_relations_in_one_query(client, catalog):
    workshop, user = catalog
    booking = create_booking(workshop.pk, user)
    with CaptureQueriesContext(connection) as queries:
        response = client.get(f"/bookings/{booking.pk}/")
    assert response.status_code == 200
    assert len(queries) == 1
    assert "JOIN" in queries[0]["sql"]


def test_statistics_include_objects_without_bookings(client, catalog):
    _, user = catalog
    Master.objects.create(name="Мастер без занятий")
    assert "Мастер без занятий" in (
        client.get("/workshops/masters/").content.decode()
    )
    stats = client.get("/bookings/statistics/")
    assert list(stats.context["users"])[0].active_count == 0
    assert user.name in stats.content.decode()


def test_database_enforces_active_uniqueness(catalog):
    from django.db import IntegrityError
    workshop, user = catalog
    create_booking(workshop.pk, user)
    with pytest.raises(IntegrityError), transaction.atomic():
        Booking.objects.create(workshop=workshop, user=user)


def test_edits_preserve_existing_booking_rules(catalog):
    workshop, user = catalog
    create_booking(workshop.pk, user)
    user.age = 10
    with pytest.raises(ValidationError):
        user.full_clean()
    workshop.capacity = 0
    with pytest.raises(ValidationError):
        workshop.full_clean()
    workshop.capacity = 2
    workshop.minimum_age = 20
    with pytest.raises(ValidationError):
        workshop.full_clean()


def test_missing_foreign_keys_produce_validation_errors():
    booking = Booking(workshop_id=999, user_id=999)
    with pytest.raises(ValidationError):
        booking.full_clean()
