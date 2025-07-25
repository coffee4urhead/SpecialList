from django.urls import path
from .views import AdminDashboardView, CoreInfoView, ServicesInfoView

urlpatterns = [
    path('', AdminDashboardView.as_view(), name='custom_admin_home'),
    path('core-info/', CoreInfoView.as_view(), name='admin_core_info'),
    path('services-info/', ServicesInfoView.as_view(), name='admin_services_info'),
]
