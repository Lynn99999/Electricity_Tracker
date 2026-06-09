from datetime import timedelta

from django.core.management import call_command

from powertracker.helpers.mm_time import get_current_myanmar_time
from powertracker.helpers.report_window import get_report_window
from powertracker.models import Schedule, Township, TownshipStatistics


MIN_REPORTS_TO_UPDATE = 3


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


def is_schedule_start_window(myanmar_now):
    window_start, window_end = get_report_window(myanmar_now)
    window_date = window_start.date()
    start_time = window_start.time()
    end_time = window_end.time()

    if start_time < end_time:
        return Schedule.objects.filter(
            date=window_date,
            start_time__gte=start_time,
            start_time__lt=end_time,
        ).exists()

    return Schedule.objects.filter(
        date=window_date,
        start_time__gte=start_time,
    ).exists() or Schedule.objects.filter(
        date=window_end.date(),
        start_time__lt=end_time,
    ).exists()


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


def get_majority_status(statistic):
    reported_on_count = statistic.reported_on_count
    reported_off_count = statistic.reported_off_count
    total_count = reported_on_count + reported_off_count

    if total_count <= MIN_REPORTS_TO_UPDATE:
        return None

    if reported_on_count > reported_off_count:
        return "ON"
    elif reported_off_count > reported_on_count:
        return "OFF"

    return None


def get_township_statistic_for_window(township, window_start, window_end):
    return (
        TownshipStatistics.objects
        .filter(
            township=township,
            start_time=window_start,
            end_time=window_end,
        )
        .order_by("-id")
        .first()
    )


def get_status_from_statistic(township, statistic, expected_status):
    majority_status = get_majority_status(statistic)

    if majority_status is None:
        return township.current_status

    if township.current_status == "ON":
        if majority_status == "ON":
            return "ON"

        return "UNCERTAIN"

    if township.current_status == "OFF":
        if majority_status == "OFF":
            return "OFF"

        return "UNCERTAIN"

    if township.current_status != "UNCERTAIN":
        return township.current_status

    if expected_status == "ON":
        if majority_status == "ON":
            return "ON"

        return "UNCERTAIN"

    if expected_status == "OFF":
        if majority_status == "OFF":
            return "OFF"

        return "UNCERTAIN"

    return township.current_status


def update_township_statuses_from_reports():
    call_command("process_reports")

    myanmar_now = get_current_myanmar_time()
    current_schedule = get_current_schedule()
    current_window_start, _ = get_report_window(myanmar_now)
    statistic_window_start = current_window_start - timedelta(minutes=5)
    statistic_window_end = current_window_start

    if is_schedule_start_window(myanmar_now):
        update_township_statuses()
        return {
            "mode": "schedule",
            "updated_count": Township.objects.count(),
        }

    updated_count = 0

    for township in Township.objects.all():
        statistic = get_township_statistic_for_window(
            township,
            statistic_window_start,
            statistic_window_end,
        )

        if statistic is None:
            continue

        expected_status = get_expected_status_for_township(
            township,
            current_schedule
        )
        new_status = get_status_from_statistic(
            township,
            statistic,
            expected_status
        )

        if township.current_status == new_status:
            continue

        township.current_status = new_status
        township.save(update_fields=["current_status", "updated_at"])
        updated_count += 1

    return {
        "mode": "reports",
        "updated_count": updated_count,
    }
