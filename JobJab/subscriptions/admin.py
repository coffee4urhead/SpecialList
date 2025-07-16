from django.contrib import admin

from JobJab.subscriptions.models import Subscription


# Register your models here.
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'price', 'current_period_end', 'is_current')
    list_filter = ('plan', 'status')
    search_fields = ('user__username', 'user__email', 'stripe_customer_id', 'stripe_subscription_id')
    readonly_fields = ('created_at', 'updated_at')

    def is_current(self, obj):
        return obj.is_current
    is_current.boolean = True
    is_current.short_description = 'Active?'