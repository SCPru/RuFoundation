from django import template

register = template.Library()

@register.filter(name='list_to_string')
def list_to_string(value, separator=''):
    if isinstance(value, list):
        return separator.join(str(item) for item in value)
    return value