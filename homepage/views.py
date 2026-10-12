"""Формирование HTML и HTTP-ответов без шаблонов на этапе ПР5."""

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import escape
from django.views.decorators.http import require_safe


def page(title: str, content: str) -> str:
    """Собрать общий каркас; content — разметка из представления."""
    bootstrap = (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.8"
        "/dist/css/bootstrap.min.css"
    )
    home_url = reverse("homepage:index")
    workshops_url = reverse("workshops:list")
    bookings_url = reverse("bookings:list")
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)} | Творческая студия</title>
    <link rel="stylesheet" href="{bootstrap}">
    <style>
        body {{ font-family: system-ui, sans-serif; color: #25342f;
                background: #f5f6f2; margin: 0; line-height: 1.6; }}
        .container {{ max-width: 960px; margin: auto; padding: 24px; }}
        .site-nav {{ display: flex; gap: 20px; flex-wrap: wrap;
                     background: #fff; border-bottom: 1px solid #ddd; }}
        .site-nav a {{ color: #285d49; text-decoration: none; }}
        .card {{ border-radius: 12px; background: #fff; }}
        a {{ color: #285d49; }}
        h1 {{ margin-bottom: 24px; }}
    </style>
</head>
<body>
    <nav class="site-nav container" aria-label="Основная навигация">
        <a href="{home_url}">Главная</a>
        <a href="{workshops_url}">Занятия</a>
        <a href="{bookings_url}">Записи</a>
    </nav>
    <main class="container">{content}</main>
</body>
</html>"""


@require_safe
def index(request: HttpRequest) -> HttpResponse:
    """Показать назначение сервиса и переходы в основные разделы."""
    workshops_url = reverse("workshops:list")
    bookings_url = reverse("bookings:list")
    content = f"""
    <p class="text-secondary">Творческая студия</p>
    <h1 class="display-5">Сервис записи на творческие занятия</h1>
    <p class="lead">Рисование, керамика и работа с глиной.
        Выберите занятие и узнайте условия участия.</p>
    <div class="d-flex gap-3 flex-wrap my-4">
        <a class="btn btn-success" href="{workshops_url}">Смотреть занятия</a>
        <a class="btn btn-outline-secondary" href="{bookings_url}">
            Открыть записи</a>
    </div>
    <p>В каталоге указаны мастер, дата, стоимость, возрастное ограничение
        и свободные места. В разделе записей можно посмотреть участие
        и историю отмен.</p>
    """
    return HttpResponse(page("Главная", content))


def page_not_found(
    request: HttpRequest, exception: Exception,
) -> HttpResponse:
    """Обработать неизвестный URL при DEBUG=False."""
    home_url = reverse("homepage:index")
    content = f"""
    <h1 class="text-danger">404 — страница не найдена</h1>
    <p>Проверьте адрес или вернитесь на главную.</p>
    <a class="btn btn-outline-secondary" href="{home_url}">На главную</a>
    """
    return HttpResponse(page("Страница не найдена", content), status=404)
