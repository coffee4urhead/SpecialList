from django import template

register = template.Library()

@register.filter
def to_list(value):
    """Converts a comma-separated string to a list"""
    return [item.strip() for item in value.split(',')]
