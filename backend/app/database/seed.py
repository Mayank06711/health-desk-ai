from datetime import datetime, timedelta
from app.database.models import SlotModel


def generate_slots(start_date: datetime | None = None, days: int = 30) -> list[SlotModel]:
    """Generate appointment slots for the next N days, 9 AM to 5 PM hourly."""
    if start_date is None:
        start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        # Start from tomorrow
        start_date += timedelta(days=1)

    slots = []
    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        # Skip weekends
        if current_date.weekday() >= 5:
            continue

        date_str = current_date.strftime("%Y-%m-%d")
        for hour in range(9, 18):  # 9 AM to 5 PM
            time_str = f"{hour:02d}:00"
            slots.append(SlotModel(date=date_str, time=time_str, is_available=True))

    return slots
