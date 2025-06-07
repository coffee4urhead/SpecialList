from django import template
from ..models import Review, ReviewType

register = template.Library()


@register.inclusion_tag('review_card.html')
def show_reviews(limit=4):
    reviews = Review.objects.filter(
        review_type=ReviewType.WEBSITE.value
    ).select_related('reviewer').order_by('-created_at')[:limit]

    return {
        'reviews_from_user_to_the_website': reviews,
        'has_reviews': reviews.exists()
    }