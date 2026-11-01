"""Список занятий и детали по целочисленному ID."""

from django.urls import path

from . import views

app_name = "workshops"
urlpatterns = [
    path("", views.workshop_list, name="list"),
    path("available/", views.available_workshops, name="available"),
    path("masters/", views.master_list, name="masters"),
    path("<int:workshop_id>/", views.workshop_detail, name="detail"),
]
