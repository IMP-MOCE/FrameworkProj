"""Участник занятия с именем и возрастом."""

from django.core.validators import MaxValueValidator
from django.core.exceptions import ValidationError
from django.db import models


class User(models.Model):
    name = models.CharField("Имя", max_length=200)
    age = models.PositiveSmallIntegerField(
        "Возраст", validators=[MaxValueValidator(120)],
    )

    class Meta:
        ordering = ["name", "pk"]
        constraints = [
            models.UniqueConstraint(fields=["name", "age"],
                                    name="unique_participant"),
            models.CheckConstraint(condition=models.Q(age__lte=120),
                                   name="participant_age_range"),
        ]
        verbose_name = "Участник"
        verbose_name_plural = "Участники"

    def __str__(self):
        return f"{self.name}, {self.age} лет"

    def clean(self):
        super().clean()
        if self.pk and self.age is not None and self.bookings.filter(
            workshop__minimum_age__gt=self.age,
        ).exists():
            raise ValidationError(
                "Возраст ниже ограничения записанных занятий.",
            )
