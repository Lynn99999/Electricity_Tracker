from datetime import timedelta

from powertracker.helpers.mm_time import get_current_myanmar_time
from powertracker.models import Schedule, Township


def is_schedule_active(schedule, current_time):
    if schedule.start_time < schedule.end_time:
        return schedule.start_time <= current_time < schedule.end_time

    return current_time >= schedule.start_time or current_time < schedule.end_time


def get_current_schedule():
    myanmar_now = get_current_myanmar_time()
    today = myanmar_now.date()
    current_time = myanmar_now.time()

    schedules = Schedule.objects.filter(date=today)

    for schedule in schedules:
        if is_schedule_active(schedule, current_time):
            return schedule

    yesterday = today - timedelta(days=1)
    yesterday_schedules = Schedule.objects.filter(date=yesterday)

    for schedule in yesterday_schedules:
        if schedule.start_time > schedule.end_time and current_time < schedule.end_time:
            return schedule

    return None


def get_expected_status_for_township(township, current_schedule):
    if current_schedule is None:
        return "UNCERTAIN"

    if current_schedule.active_group == "All":
        return "ON"

    if township.group == current_schedule.active_group:
        return "ON"

    return "OFF"


def update_township_statuses():
    current_schedule = get_current_schedule()
    townships = Township.objects.all()

    for township in townships:
        new_status = get_expected_status_for_township(
            township,
            current_schedule
        )

        if township.current_status != new_status:
            township.current_status = new_status
            township.save(update_fields=["current_status", "updated_at"])

