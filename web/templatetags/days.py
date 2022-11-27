from datetime import date, datetime

from django import template
from django.utils.translation import gettext as _


register = template.Library()


@register.filter(expects_localtime=True)
def days_since(value, arg=None):
    try:
        tzinfo = getattr(value, 'tzinfo', None)
        value = date(value.year, value.month, value.day)
    except AttributeError:
        # Passed value wasn't a date object
        return value
    except ValueError:
        # Date arguments out of range
        return value
    today = datetime.now(tzinfo).date()
    delta = value - today

    if abs(delta.days) % 10 == 1:
        day_str = "день"
    elif abs(delta.days) % 10 in range(2, 5):
        day_str = "дня"
    else:
        day_str = "дней"

    if delta.days < 1:
        fa_str = "назад"
    else:
        fa_str = "после сегодня"

    return "%s %s %s" % (abs(delta.days), day_str, fa_str)
