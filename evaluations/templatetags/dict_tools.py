from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def get_item(mapping, key):
    if not mapping:
        return None
    return mapping.get(key)


@register.filter
def stars_html(value):
    """Render filled/empty star icons for a 1–5 integer rating."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return ''
    filled = '★' * n
    empty = '☆' * (5 - n)
    return mark_safe(
        f'<span class="stars-rating" aria-label="{n} نجوم">'
        f'<span class="stars-filled">{filled}</span>'
        f'<span class="stars-empty">{empty}</span>'
        f'</span>'
    )
