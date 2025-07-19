from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('offerSubscriptions/', views.offer_plans, name='offer_plans'),
    path('create-checkout-session/<str:plan_type>/', views.create_checkout_session, name='create-checkout-session'),
    path('success/', views.success_view, name='success'),
    path('canceled/', views.canceled_view, name='canceled'),
    re_path(r'^stripe-webhook/?$', views.stripe_webhook, name='stripe-webhook'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
