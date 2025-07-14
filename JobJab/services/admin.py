from django.contrib import admin, messages
from JobJab.services.models import ServiceListing, Comment


@admin.register(ServiceListing)
class ServiceListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'category', 'price', 'duration_minutes', 'is_active', 'created_at')
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('title', 'description', 'provider__username')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('likes', 'comments')

    fieldsets = (
        (None, {
            'fields': (
                'provider',
                'title',
                'description',
                'service_photo',
                'category',
                'price',
                'duration_minutes',
                'is_active',
            )
        }),
        ('Likes', {
            'fields': ('likes',),
            'classes': ('collapse',),
        }),
        ('Comments', {
            'fields': ('comments',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'short_content', 'is_reply', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('author__username', 'content')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    actions = ['delete_all_comments']

    def short_content(self, obj):
        return obj.content[:75] + ('...' if len(obj.content) > 75 else '')

    short_content.short_description = 'Content'

    @admin.action(description="❌ Delete all comments")
    def delete_all_comments(self, request, queryset):
        count = Comment.objects.all().count()
        Comment.objects.all().delete()
        self.message_user(request, f"Successfully deleted all {count} comments.", messages.SUCCESS)
