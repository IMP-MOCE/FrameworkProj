"""Справочник мастеров."""

from django.db import models


class Master(models.Model):
    name = models.CharField("Имя", max_length=200, unique=True)

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "Мастер"
        verbose_name_plural = "Мастера"

    def __str__(self):
        return self.name
