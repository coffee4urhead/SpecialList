from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone

from JobJab.subscriptions.models import Subscription
from JobJab.core.models import CustomUser, Organization, UserLocation, Certificate, NotificationType, BlacklistStatus, \
    BlacklistReason, UserBlacklistProfile, Notification, BlacklistItem


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


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at', 'related_object')
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'message', 'notification_type', 'is_read')
        }),
        ('Related Content', {
            'fields': ('related_content_type', 'related_object_id', 'related_object'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    date_hierarchy = 'created_at'
    list_per_page = 20

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(BlacklistItem)
class BlacklistItemAdmin(admin.ModelAdmin):
    list_display = ('content_object', 'get_reason_display', 'status', 'reporter', 'created_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('description', 'moderator_notes', 'reporter__username')
    readonly_fields = ('created_at', 'updated_at', 'resolved_at', 'content_object')
    fieldsets = (
        ('Report Details', {
            'fields': ('reporter', 'content_type', 'object_id', 'content_object')
        }),
        ('Moderation', {
            'fields': ('reason', 'description', 'status', 'moderator', 'moderator_notes')
        }),
        ('Actions', {
            'fields': ('auto_hidden',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        })
    )
    actions = ['approve_reports', 'reject_reports', 'mark_as_warning']
    date_hierarchy = 'created_at'
    list_per_page = 20

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('reporter', 'moderator', 'content_type')

    def approve_reports(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='approved',
            moderator=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(request, f"{updated} reports approved and content hidden.")

    approve_reports.short_description = "Approve selected reports"

    def reject_reports(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='rejected',
            moderator=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(request, f"{updated} reports rejected.")

    reject_reports.short_description = "Reject selected reports"

    def mark_as_warning(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='warning',
            moderator=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(request, f"{updated} reports marked as warnings.")

    mark_as_warning.short_description = "Mark as warning"


@admin.register(UserBlacklistProfile)
class UserBlacklistProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_banned', 'warning_count', 'last_warning', 'banned_at')
    list_filter = ('is_banned',)
    search_fields = ('user__username', 'ban_reason')
    readonly_fields = ('last_warning', 'banned_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'is_banned', 'ban_reason', 'banned_by')
        }),
        ('Warnings', {
            'fields': ('warning_count', 'last_warning'),
            'classes': ('collapse',)
        }),
        ('Ban Details', {
            'fields': ('banned_at',),
            'classes': ('collapse',)
        })
    )
    actions = ['ban_users', 'unban_users', 'reset_warnings']
    list_per_page = 20

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'banned_by')

    def ban_users(self, request, queryset):
        for profile in queryset:
            profile.ban_user(request.user, "Banned via admin action")
        self.message_user(request, f"{queryset.count()} users banned.")

    ban_users.short_description = "Ban selected users"

    def unban_users(self, request, queryset):
        for profile in queryset.filter(is_banned=True):
            profile.unban_user(request.user, "Unbanned via admin action")
        self.message_user(request, f"{queryset.count()} users unbanned.")

    unban_users.short_description = "Unban selected users"

    def reset_warnings(self, request, queryset):
        updated = queryset.update(warning_count=0, last_warning=None)
        self.message_user(request, f"{updated} user warnings reset.")

    reset_warnings.short_description = "Reset warning counts"
