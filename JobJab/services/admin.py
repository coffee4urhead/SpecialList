from django.contrib import admin
from JobJab.services.models import ServiceListing

@admin.register(ServiceListing)
class ServiceListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'category', 'price', 'duration_minutes', 'is_active', 'created_at')
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('title', 'description', 'provider__username')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('likes',)

    fieldsets = (
        (None, {
            'fields': ('provider', 'title', 'description', 'service_photo', 'category', 'price', 'duration_minutes', 'is_active')
        }),
        ('Likes', {
            'fields': ('likes',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
