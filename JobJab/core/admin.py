from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from JobJab.subscriptions.models import Subscription
from JobJab.core.models import CustomUser, Organization, UserLocation, Certificate


class SubscriptionInline(admin.StackedInline):
    model = Subscription
    fields = ('stripe_customer_id', 'plan')
    can_delete = False
    extra = 0

@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'latitude', 'longitude', 'last_updated')

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_staff', 'get_subscription_plan', 'last_login', 'is_active')

    def get_subscription_plan(self, obj):
        return obj.subscription.plan if hasattr(obj, 'subscription') else None

    get_subscription_plan.short_description = 'Subscription Plan'

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Account View Info', {'fields': ('bio', 'first_name', 'last_name', 'backcover_profile')}),
        ('Personal info', {'fields': ('email', 'user_type', 'profile_picture')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'user_type', 'password1', 'password2'),
        }),
    )
    inlines = [SubscriptionInline]

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'website')
    search_fields = ('name',)

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'certificate_file', 'uploaded_at', 'is_verified')