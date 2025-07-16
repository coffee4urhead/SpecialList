from django.shortcuts import get_object_or_404, render
from JobJab.subscriptions.models import SubscriptionRecord
from JobJab.core.models import CustomUser

def user_payments(request, username):
    user = get_object_or_404(CustomUser, username=username)
    payments_made = SubscriptionRecord.objects.filter(user=user).order_by('-created_at')

    context = {
        'user': user,
        'payments': payments_made,
    }

    return render(request, 'core/accounts/account-tabs/account_payments.html', context)