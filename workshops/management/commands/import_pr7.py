"""Перенос исходной базы командой manage.py import_pr7."""

import sqlite3

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from db.import_sqlite_to_orm import import_data


class Command(BaseCommand):
    help = "Перенести базу ПР7 в Django ORM с сохранением ID."

    def add_arguments(self, parser):
        parser.add_argument("--source", help="Путь к исходной studio.sqlite")

    def handle(self, *args, **options):
        try:
            counts = import_data(options["source"])
        except (ValueError, ValidationError,
                IntegrityError, sqlite3.Error) as err:
            raise CommandError(str(err)) from err
        self.stdout.write(self.style.SUCCESS(f"Перенос проверен: {counts}"))
