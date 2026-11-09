"""Запись связывает участника и занятие, отмена сохраняет историю."""

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Q


class Booking(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активна"
        CANCELLED = "cancelled", "Отменена"

    workshop = models.ForeignKey(
        "workshops.Workshop", on_delete=models.PROTECT,
        related_name="bookings",
        verbose_name="Занятие",
    )
    user = models.ForeignKey(
        "users.User", on_delete=models.PROTECT, related_name="bookings",
        verbose_name="Участник",
    )
    status = models.CharField("Статус", max_length=9, choices=Status.choices,
                              default=Status.ACTIVE)

    class Meta:
        ordering = ["workshop__date", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=["active", "cancelled"]),
                name="booking_valid_status",
            ),
            models.UniqueConstraint(
                fields=["workshop", "user"], condition=Q(status="active"),
                name="unique_active_booking",
            ),
        ]
        verbose_name = "Запись"
        verbose_name_plural = "Записи"

    def clean(self):
        super().clean()
        if not self.workshop_id or not self.user_id:
            return
        try:
            self.workshop
            self.user
        except ObjectDoesNotExist:
            # full_clean уже собирает ошибки проверки внешних ключей.
            return
        if self.user.age < self.workshop.minimum_age:
            raise ValidationError(
                "Возраст участника ниже ограничения занятия.",
            )
        if self.status == self.Status.ACTIVE:
            others = Booking.objects.filter(
                workshop_id=self.workshop_id, status=self.Status.ACTIVE,
            ).exclude(pk=self.pk)
            if others.count() >= self.workshop.capacity:
                raise ValidationError("Свободных мест нет.")
            for other in others.select_related("user"):
                if (other.user.name.casefold(), other.user.age) == (
                    self.user.name.casefold(), self.user.age,
                ):
                    raise ValidationError(
                        "Этот участник уже записан на занятие.",
                    )

    def cancel(self):
        if self.status == self.Status.CANCELLED:
            raise ValidationError("Запись уже отменена.")
        self.status = self.Status.CANCELLED
        self.save(update_fields=["status"])

    def __str__(self):
        return f"Запись №{self.pk}: {self.user} — {self.workshop}"
