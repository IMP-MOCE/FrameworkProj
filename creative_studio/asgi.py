"""Точка входа для ASGI-сервера."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "creative_studio.settings")
application = get_asgi_application()
