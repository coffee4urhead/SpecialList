from django.contrib import admin
from JobJab.reviews.models import WebsiteReview, UserReview


# Register your models here.
@admin.register(WebsiteReview)
class WebsiteReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'rating', 'main_caption', 'comment', 'created_at', 'updated_at')
    list_filter = ('reviewer', 'created_at', 'updated_at')

@admin.register(UserReview)
class UserReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'reviewee', 'rating', 'main_caption', 'comment', 'created_at', 'updated_at')
    list_filter = ('reviewer', 'created_at', 'updated_at')

