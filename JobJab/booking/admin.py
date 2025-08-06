from django.contrib import admin
from .models import ProviderAvailability, WeeklyTimeSlot, Booking


@admin.register(ProviderAvailability)
class ProviderAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('provider', 'slot_duration', 'buffer_time', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('provider__username', 'provider__email')
    raw_id_fields = ('provider',)


@admin.register(WeeklyTimeSlot)
class WeeklyTimeSlotAdmin(admin.ModelAdmin):
    list_display = ('availability', 'get_day_of_week', 'start_time', 'end_time', 'is_booked')
    list_filter = ('day_of_week', 'is_booked')
    search_fields = ('availability__provider__username',)
    list_editable = ('is_booked',)

    def get_day_of_week(self, obj):
        return obj.get_day_of_week_display()

    get_day_of_week.short_name = 'Day'
    get_day_of_week.admin_order_field = 'day_of_week'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'seeker',
        'provider',
        'service',
        'appointment_datetime',
        'status',
        'payment_status',
        'price',
        'created_at'
    )
    list_filter = (
        'status',
        'payment_status',
        'appointment_datetime',
        'created_at'
    )
    search_fields = (
        'seeker__username',
        'provider__username',
        'service__title',
        'stripe_payment_intent_id'
    )
    raw_id_fields = ('seeker', 'provider', 'service', 'time_slot')
    date_hierarchy = 'appointment_datetime'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('seeker', 'provider', 'service', 'time_slot')
        }),
        ('Appointment Details', {
            'fields': ('appointment_datetime', 'status', 'notes')
        }),
        ('Payment Information', {
            'fields': (
                'price',
                'payment_status',
                'amount_paid',
                'stripe_payment_intent_id',
                'stripe_customer_id',
                'stripe_invoice_id'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if obj.time_slot:
            obj.price = obj.calculate_price()
        super().save_model(request, obj, form, change)