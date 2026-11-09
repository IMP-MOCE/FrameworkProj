"""Занятия и вычисление числа свободных мест через ORM."""

from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, F, Q


class WorkshopQuerySet(models.QuerySet):
    def with_seats(self):
        return self.annotate(
            active_count=Count(
                "bookings", filter=Q(bookings__status="active"),
            ),
        ).annotate(seats=F("capacity") - F("active_count"))


class Workshop(models.Model):
    name = models.CharField("Название", max_length=200)
    master = models.ForeignKey("masters.Master", on_delete=models.PROTECT,
                               related_name="workshops", verbose_name="Мастер")
    date = models.DateField("Дата")
    price = models.DecimalField(
        "Стоимость", max_digits=9, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(1000000)],
    )
    capacity = models.PositiveIntegerField(
        "Вместимость",
        validators=[MinValueValidator(1), MaxValueValidator(10000)],
    )
    minimum_age = models.PositiveSmallIntegerField(
        "Минимальный возраст", default=0, validators=[MaxValueValidator(120)],
    )
    description = models.TextField("Описание", blank=True, null=True)
    objects = WorkshopQuerySet.as_manager()

    class Meta:
        ordering = ["date", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(capacity__gte=1, capacity__lte=10000),
                name="workshop_capacity_range",
            ),
            models.CheckConstraint(condition=Q(minimum_age__lte=120),
                                   name="workshop_age_range"),
            models.CheckConstraint(
                condition=Q(price__gte=0, price__lte=1000000),
                name="workshop_price_range",
            ),
        ]
        verbose_name = "Занятие"
        verbose_name_plural = "Занятия"

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if not self.pk:
            return
        if self.capacity is not None and self.bookings.filter(
            status="active",
        ).count() > self.capacity:
            raise ValidationError(
                "Вместимость меньше числа активных записей.",
            )
        if self.minimum_age is not None and self.bookings.filter(
            user__age__lt=self.minimum_age,
        ).exists():
            raise ValidationError("На занятие записаны участники младше порога.")
