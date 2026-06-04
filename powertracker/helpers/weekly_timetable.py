from datetime import timedelta

from powertracker.helpers.mm_time import get_current_myanmar_time
from powertracker.models import Schedule


def format_date(date):
    return date.strftime("%d %b, %Y")


def format_time(time):
    return time.strftime("%I%p").lstrip("0")


def get_slot_status(township, schedule):
    if schedule.active_group == "All":
        return "ON"

    if schedule.active_group == township.group:
        return "ON"

    return "OFF"


def get_weekly_timetable_for_township(township):
    today = get_current_myanmar_time().date()
    start_date = today - timedelta(days=1)
    end_date = today + timedelta(days=7)

    schedules = Schedule.objects.filter(
        date__range=(start_date, end_date)
    ).order_by("date", "start_time")

    schedules_by_date = {}

    for schedule in schedules:
        schedules_by_date.setdefault(schedule.date, []).append(schedule)

    timetable = []
    current_date = start_date

    while current_date <= end_date:
        day_schedules = schedules_by_date.get(current_date, [])
        slots = []

        for schedule in day_schedules:
            slots.append({
                "time": f"{format_time(schedule.start_time)} - {format_time(schedule.end_time)}",
                "status": get_slot_status(township, schedule),
            })

        timetable.append({
            "date": format_date(current_date),
            "day": current_date.strftime("%A"),
            "is_today": current_date == today,
            "is_yesterday": current_date == today - timedelta(days=1),
            "slots": slots,
        })

        current_date += timedelta(days=1)

    return timetable
