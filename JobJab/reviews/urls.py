from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('user/<str:username>/leaveReview/', views.leave_user_review, name='leave_review'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
