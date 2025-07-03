from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('subscription/checkout/', views.create_checkout_session, name='create-checkout'),
    path('subscription/success/', views.success_view, name='success'),
    path('subscription/canceled/', views.canceled_view, name='canceled'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe-webhook'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
