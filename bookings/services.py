"""Создание записи с проверками правил ПР3 и транзакцией."""

from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from workshops.models import Workshop
from .models import Booking


@transaction.atomic
def create_booking(workshop_id, user):
    workshop = Workshop.objects.select_for_update().get(pk=workshop_id)
    # На SQLite запись резервирует блокировку до проверки количества мест.
    Workshop.objects.filter(pk=workshop.pk).update(capacity=F("capacity"))
    if workshop.date < date.today():
        raise ValidationError("Дата занятия уже прошла.")
    booking = Booking(workshop=workshop, user=user)
    booking.full_clean()
    booking.save()
    return booking
