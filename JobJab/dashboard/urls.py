from django.urls import path

from JobJab.dashboard.views import AdminDashboardView
from JobJab.dashboard.views.disputes import ResolveDisputes
from JobJab.dashboard.views.info_views.booking import BookingInfoView
from JobJab.dashboard.views.info_views.chats import ChatsInfoView
from JobJab.dashboard.views.info_views.core import CoreInfoView
from JobJab.dashboard.views.info_views.reviews import ReviewsInfoView
from JobJab.dashboard.views.info_views.services import ServicesInfoView
from JobJab.dashboard.views.info_views.subscriptions import SubscriptionsInfoView

urlpatterns = [
    path('', AdminDashboardView.as_view(), name='custom_admin_home'),
    path('core-info/', CoreInfoView.as_view(), name='admin_core_info'),
    path('services-info/', ServicesInfoView.as_view(), name='admin_services_info'),
    path('subscription-info/', SubscriptionsInfoView.as_view(), name='admin_subscriptions_info'),
    path('chats-info/', ChatsInfoView.as_view(), name='admin_chats_info'),
    path('reviews-info/', ReviewsInfoView.as_view(), name='admin_reviews_info'),
    path('bookings-info/', BookingInfoView.as_view(), name='admin_bookings_info'),
    path('resolve-dispute/', ResolveDisputes.as_view(), name='admin_resolve_dispute'),
    path('resolve-dispute/<int:dispute_id>/<str:action>/', ResolveDisputes.as_view(), name='admin_resolved_dispute'),
]
