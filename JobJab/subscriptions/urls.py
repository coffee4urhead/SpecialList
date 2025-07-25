from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    OfferPlansView,
    CreateCheckoutSessionView,
    SuccessView,
    CanceledView,
    StripeWebhookView
)

urlpatterns = [
    path('offerSubscriptions/', OfferPlansView.as_view(), name='offer_plans'),
    path('create-checkout-session/<str:plan_type>/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('success/', SuccessView.as_view(), name='success'),
    path('canceled/', CanceledView.as_view(), name='canceled'),
    re_path(r'^stripe-webhook/?$', StripeWebhookView.as_view(), name='stripe-webhook'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
