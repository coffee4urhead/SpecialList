from django import template
from django.templatetags.static import static

register = template.Library()

@register.inclusion_tag('template-components/flip-component.html')
def flip_component(image=None, heading=None, text=None, flip=False, alt_text=None):
    return {
        'image_url': static(image) if image else None,
        'heading': heading,
        'text': text,
        'flip': flip,
        'alt_text': alt_text
    }