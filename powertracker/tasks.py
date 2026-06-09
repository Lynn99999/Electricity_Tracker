from celery import shared_task
from django.core.management import call_command

from powertracker.helpers.check_status import update_township_statuses_from_reports
from powertracker.helpers.push_notifications import send_schedule_notifications


@shared_task
def process_completed_report_windows():
    call_command("process_reports")


@shared_task
def update_township_statuses_task():
    return update_township_statuses_from_reports()


@shared_task
def send_schedule_notifications_task():
    return send_schedule_notifications()
