from django_cron import CronJobBase, Schedule
from django.utils import timezone
from JobJab.subscriptions.models import Subscription, SubscriptionStatus


class CheckOverdueSubscriptionsCronJob(CronJobBase):
    RUN_EVERY_MINS = 60 * 24

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'subscriptions.check_overdue_subscriptions'

    def do(self):
        now = timezone.now()
        overdue_subs = Subscription.objects.filter(
            current_period_end__lt=now,
            is_active=True,
        )

        for sub in overdue_subs:
            sub.status = SubscriptionStatus.PAST_DUE
            sub.is_active = False
            sub.save()
            print(f"Marked subscription {sub.id} as PAST_DUE")
