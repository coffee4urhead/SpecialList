from django.urls import path
from .views import create_booking, get_time_slots, create_availability_view, stripe_webhook, create_payment_intent, \
    booking_confirmation, verify_payment

app_name = 'booking'

urlpatterns = [
    path('create/', create_booking, name='create_booking'),
    path('<int:service_id>/slots/', get_time_slots, name='time_slots'),
    path('availability/', create_availability_view, name='set_availability'),
    path('payments/create-intent/<int:booking_id>/', create_payment_intent, name='create_payment_intent'),
    path('booking-confirmed/<int:booking_id>/', booking_confirmation, name='booking_confirmed'),
    path('verify-payment/<int:booking_id>/', verify_payment, name='verify_payment'),
    path('stripe-webhook/', stripe_webhook, name='stripe_webhook'),
]
