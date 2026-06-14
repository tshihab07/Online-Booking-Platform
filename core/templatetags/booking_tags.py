from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()


@register.filter
def currency(value, symbol='$'):
    try:
        return f"{symbol}{float(value):,.2f}"
    except (TypeError, ValueError):
        return value


@register.filter
def duration_display(minutes):
    try:
        minutes = int(minutes)
        if minutes < 60:
            return f"{minutes}min"
        h, m = divmod(minutes, 60)
        return f"{h}h {m}min" if m else f"{h}h"
    except (TypeError, ValueError):
        return f"{minutes}min"


@register.filter
def json_script_safe(value):
    return mark_safe(json.dumps(value))


@register.simple_tag
def theme_css_vars(business):
    if not business:
        return mark_safe('')
    colors = business.brand_colors or {}
    primary = colors.get('primary', '#6366f1')
    secondary = colors.get('secondary', '#8b5cf6')
    accent = colors.get('accent', '#06b6d4')
    css = f"""
    <style>
        :root {{
            --color-primary: {primary};
            --color-secondary: {secondary};
            --color-accent: {accent};
        }}
    </style>
    """
    return mark_safe(css)


@register.inclusion_tag('core/partials/star_rating.html')
def star_rating(rating, max_stars=5):
    full = int(rating)
    half = 1 if (rating - full) >= 0.5 else 0
    empty = max_stars - full - half
    return {'full': range(full), 'half': half, 'empty': range(empty)}


@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter — used in templates."""
    if value:
        return value.split(delimiter)
    return []


@register.filter
def slot_status_class(count, max_count):
    try:
        ratio = int(count) / int(max_count)
        if ratio >= 0.8:
            return 'slot-red'
        elif ratio >= 0.5:
            return 'slot-orange'
        return 'slot-green'
    except (TypeError, ValueError, ZeroDivisionError):
        return 'slot-green'
