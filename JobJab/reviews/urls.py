from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import LeaveUserReviewView, EditUserReviewView, DeleteUserReviewView

urlpatterns = [
                  path('user/<str:username>/leaveReview/', LeaveUserReviewView.as_view(), name='leave_review'),
                  path('user/<str:username>/editReview/<int:review_id>/', EditUserReviewView.as_view(),
                       name='edit_user_review'),
                  path('user/<str:username>/deleteReview/<int:review_id>/', DeleteUserReviewView.as_view(),
                       name='delete_user_review'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
