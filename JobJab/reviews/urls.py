from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
                  path('user/<str:username>/leaveReview/', views.leave_user_review, name='leave_review'),
                  path('user/<str:username>/editReview/<int:review_id>/', views.edit_user_review, name='edit_user_review'),
                  path('user/<str:username>/deleteReview/<int:review_id>/', views.delete_user_review, name='delete_user_review'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
