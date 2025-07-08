from datetime import datetime
from pytz import timezone

from JobJab.booking.models import WeeklyTimeSlot


def get_localized_slots(provider, timezone_str='UTC'):
    tz = timezone(timezone_str)
    slots = provider.availability.time_slots.filter(is_booked=False)

    return [{
        'day': WeeklyTimeSlot.DAYS_OF_WEEK[slot.day_of_week],
        'start': tz.localize(datetime.combine(datetime.today(), slot.start_time)),
        'end': tz.localize(datetime.combine(datetime.today(), slot.end_time))
    } for slot in slots]