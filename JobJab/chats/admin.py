from django.contrib import admin
from .models import Conversation, Message, UserStatus
from django.contrib.auth import get_user_model
from django.utils.html import format_html

User = get_user_model()


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'timestamp', 'preview_content')
    fields = ('sender', 'preview_content', 'timestamp', 'read')

    def preview_content(self, obj):
        content = obj.content or ""
        media = ""
        if obj.image:
            media = f"<div><img src='{obj.image.url}' style='max-height: 50px;'/></div>"
        return format_html(f"{content[:50]}...{media}")

    preview_content.short_description = 'Content'


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'participants_list', 'created_at', 'updated_at', 'last_message')
    list_filter = ('created_at',)
    search_fields = ('participants__username', 'participants__email')
    filter_horizontal = ('participants',)
    inlines = [MessageInline]

    def participants_list(self, obj):
        return ", ".join([user.username for user in obj.participants.all()])

    participants_list.short_description = 'Participants'

    def last_message(self, obj):
        last_msg = obj.get_last_message()
        return last_msg.content[:50] + "..." if last_msg else None

    last_message.short_description = 'Last Message'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'preview_content', 'timestamp', 'read')
    list_filter = ('read', 'timestamp')
    search_fields = ('content', 'sender__username')
    list_editable = ('read',)
    readonly_fields = ('timestamp', 'preview_media')
    fieldsets = (
        (None, {
            'fields': ('conversation', 'sender', 'content')
        }),
        ('Status', {
            'fields': ('read', 'timestamp')
        }),
        ('Media', {
            'fields': ('image', 'video', 'preview_media'),
            'classes': ('collapse',)
        }),
    )

    def preview_content(self, obj):
        return obj.content[:50] + '...' if obj.content else ""

    preview_content.short_description = 'Content'

    def preview_media(self, obj):
        if obj.image:
            return format_html(f'<img src="{obj.image.url}" style="max-height: 200px;"/>')
        elif obj.video:
            return format_html(f'<video width="200" controls><source src="{obj.video.url}"></video>')
        return "-"

    preview_media.short_description = 'Media Preview'


@admin.register(UserStatus)
class UserStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'online_status', 'last_seen')
    list_filter = ('online',)
    search_fields = ('user__username',)
    readonly_fields = ('last_seen', 'online_status')

    def online_status(self, obj):
        return format_html(
            '<span style="color: {};">●</span> {}',
            'green' if obj.online else 'gray',
            'Online' if obj.online else 'Offline'
        )

    online_status.short_description = 'Status'