from django import template
from django.templatetags.static import static

register = template.Library()

@register.inclusion_tag('template-components/subscription-card.html')
def card_component(title, subtitle_pricing, subscription_caption, list_of_features):
    return {
        'title': title if title is not None else None,
        'subtitle_pricing': subtitle_pricing if subtitle_pricing is not None else None,
        'subscription_caption': subscription_caption,
        'list_of_features': list_of_features
    }