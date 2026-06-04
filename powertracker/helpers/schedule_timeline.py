from datetime import datetime, timedelta

from django.utils import timezone

from powertracker.helpers.mm_time import get_current_myanmar_time
from powertracker.models import Schedule


def get_group_status(active_group):
    if active_group == "All":
        return {
            "group_a_status": "ON",
            "group_b_status": "ON",
        }

    if active_group == "A":
        return {
            "group_a_status": "ON",
            "group_b_status": "OFF",
        }

    if active_group == "B":
        return {
            "group_a_status": "OFF",
            "group_b_status": "ON",
        }

    return {
        "group_a_status": "OFF",
        "group_b_status": "OFF",
    }


def get_schedule_datetimes(schedule):
    schedule_start = datetime.combine(schedule.date, schedule.start_time)
    schedule_end = datetime.combine(schedule.date, schedule.end_time)

    if schedule.end_time <= schedule.start_time:
        schedule_end += timedelta(days=1)

    if timezone.is_aware(get_current_myanmar_time()):
        schedule_start = timezone.make_aware(schedule_start)
        schedule_end = timezone.make_aware(schedule_end)

    return schedule_start, schedule_end


def get_active_group_at_time(target_datetime, schedules):
    for schedule in schedules:
        schedule_start, schedule_end = get_schedule_datetimes(schedule)

        if schedule_start <= target_datetime < schedule_end:
            return schedule.active_group

    return None


def get_next_full_hour(current_datetime):
    next_hour = current_datetime.replace(minute=0, second=0, microsecond=0)

    if next_hour <= current_datetime:
        next_hour += timedelta(hours=1)

    return next_hour


def format_hour_label(target_datetime):
    return target_datetime.strftime("%I%p").lstrip("0")


def get_upcoming_24h_points():
    start_datetime = get_current_myanmar_time()
    end_datetime = start_datetime + timedelta(hours=24)
    current_schedule_end = None

    dates = [
        start_datetime.date() - timedelta(days=1),
        start_datetime.date(),
        end_datetime.date(),
    ]

    schedules = list(
        Schedule.objects.filter(date__in=dates).order_by("date", "start_time")
    )

    for schedule in schedules:
        schedule_start, schedule_end = get_schedule_datetimes(schedule)

        if schedule_start <= start_datetime < schedule_end:
            current_schedule_end = schedule_end
            break

    timeline_points = []
    point_datetimes = [start_datetime]
    point_datetime = get_next_full_hour(start_datetime)

    while point_datetime <= end_datetime:
        point_datetimes.append(point_datetime)
        point_datetime += timedelta(hours=1)

    for index, point_datetime in enumerate(point_datetimes):
        active_group = get_active_group_at_time(point_datetime, schedules)
        is_current_period = (
            current_schedule_end is not None
            and point_datetime < current_schedule_end
        )

        timeline_points.append({
            "label": "Now" if index == 0 else format_hour_label(point_datetime),
            "active_group": active_group,
            "is_current_period": is_current_period,
        })

    return timeline_points


def get_upcoming_24h_timeline():
    start_datetime = get_current_myanmar_time()
    end_datetime = start_datetime + timedelta(hours=24)

    dates = [
        start_datetime.date() - timedelta(days=1),
        start_datetime.date(),
        end_datetime.date(),
    ]

    schedules = Schedule.objects.filter(
        date__in=dates
    ).order_by("date", "start_time")

    timeline_items = []

    for schedule in schedules:
        schedule_start, schedule_end = get_schedule_datetimes(schedule)

        if schedule_start < end_datetime and schedule_end > start_datetime:
            status = get_group_status(schedule.active_group)

            timeline_items.append({
                "date": schedule.date,
                "start": schedule_start.strftime("%H:%M"),
                "end": schedule_end.strftime("%H:%M"),
                "active_group": schedule.active_group,
                "group_a_status": status["group_a_status"],
                "group_b_status": status["group_b_status"],
            })

    return timeline_items
