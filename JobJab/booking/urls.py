from django.urls import path
from .views import create_booking, get_time_slots, create_availability_view, stripe_webhook, create_payment_intent

app_name = 'booking'

urlpatterns = [
    path('create/', create_booking, name='create_booking'),
    path('<int:service_id>/slots/', get_time_slots, name='time_slots'),
    path('availability/', create_availability_view, name='set_availability'),
    path('payments/create-intent/<int:booking_id>/', create_payment_intent, name='create_payment_intent'),
    path('stripe-webhook/', stripe_webhook, name='stripe_webhook'),
]