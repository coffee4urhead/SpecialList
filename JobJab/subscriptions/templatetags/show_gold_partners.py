from django import template

from JobJab.core.models import UserChoices
from JobJab.subscriptions.models import Subscription, SubscriptionPlan

register = template.Library()


@register.inclusion_tag('gold_partners_template.html')
def show_gold_partners():
    gold_partners = Subscription.objects.filter(
        plan=SubscriptionPlan.ELITE.value,
        user__user_type=UserChoices.Provider.value,
    ).select_related('user')

    return {
        'gold_partners': gold_partners,
    }