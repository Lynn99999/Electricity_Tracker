import json
from datetime import datetime, timedelta

from django.conf import settings
from pywebpush import WebPushException, webpush

from powertracker.helpers.check_status import (
    get_current_schedule,
    get_expected_status_for_township,
)
from powertracker.helpers.mm_time import get_current_myanmar_time
from powertracker.models import (
    FavoriteTownship,
    Schedule,
    ScheduleNotification,
    UserProfile,
    UserPushSubscription,
)


SCHEDULE_NOTICE_MINUTES = 15


def get_first_favorite_for_user(user):
    profile = UserProfile.objects.filter(user=user).first()

    if profile is None:
        return None

    favorite = (
        FavoriteTownship.objects
        .filter(user_profile=profile)
        .select_related("township")
        .order_by("position", "created_at")
        .first()
    )

    if favorite is None:
        return None

    return favorite.township


def get_schedule_start_datetime(schedule, timezone_info):
    return datetime.combine(
        schedule.date,
        schedule.start_time,
        tzinfo=timezone_info,
    )


def get_next_schedule_for_notice(myanmar_now=None):
    myanmar_now = myanmar_now or get_current_myanmar_time()
    notice_end = myanmar_now + timedelta(minutes=SCHEDULE_NOTICE_MINUTES)

    schedules = (
        Schedule.objects
        .filter(date__in=[myanmar_now.date(), notice_end.date()])
        .order_by("date", "start_time")
    )

    for schedule in schedules:
        schedule_start = get_schedule_start_datetime(
            schedule,
            myanmar_now.tzinfo,
        )

        if myanmar_now < schedule_start <= notice_end:
            return schedule, schedule_start

    return None, None


def get_expected_status_for_notice(township, schedule):
    if schedule.active_group == "All" or township.group == schedule.active_group:
        return "ON"

    return "OFF"


def get_push_payload(township, schedule, schedule_start, next_status):
    schedule_time = schedule_start.strftime("%-I:%M %p")

    return {
        "title": "Electricity schedule reminder",
        "body": (
            f"{township.name} will switch {next_status} at {schedule_time}."
        ),
        "url": f"/townships/{township.id}/",
        "tag": f"schedule-{township.id}-{schedule.id}",
    }


def send_web_push(subscription, payload):
    vapid_private_key = getattr(settings, "VAPID_PRIVATE_KEY", "")
    vapid_admin_email = getattr(settings, "VAPID_ADMIN_EMAIL", "")

    if not vapid_private_key or not vapid_admin_email:
        return False

    subscription_info = {
        "endpoint": subscription.endpoint,
        "keys": {
            "p256dh": subscription.p256dh,
            "auth": subscription.auth,
        },
    }

    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=vapid_private_key,
            vapid_claims={
                "sub": f"mailto:{vapid_admin_email}",
            },
        )
    except WebPushException:
        subscription.is_active = False
        subscription.save(update_fields=["is_active", "updated_at"])
        return False

    return True


def send_schedule_notifications():
    schedule, schedule_start = get_next_schedule_for_notice()
    current_schedule = get_current_schedule()

    if schedule is None:
        return {
            "sent_count": 0,
            "reason": "no upcoming schedule",
        }

    sent_count = 0
    skipped_no_change_count = 0
    users_with_subscriptions = (
        UserPushSubscription.objects
        .filter(is_active=True)
        .select_related("user")
        .values_list("user", flat=True)
        .distinct()
    )

    for user_id in users_with_subscriptions:
        subscriptions = UserPushSubscription.objects.filter(
            user_id=user_id,
            is_active=True,
        )

        if not subscriptions.exists():
            continue

        user = subscriptions.first().user
        township = get_first_favorite_for_user(user)

        if township is None:
            continue

        current_status = get_expected_status_for_township(
            township,
            current_schedule,
        )
        next_status = get_expected_status_for_notice(township, schedule)

        if current_status == next_status:
            skipped_no_change_count += 1
            continue

        if ScheduleNotification.objects.filter(
            user=user,
            township=township,
            schedule=schedule,
        ).exists():
            continue

        payload = get_push_payload(
            township,
            schedule,
            schedule_start,
            next_status,
        )
        user_sent_count = 0

        for subscription in subscriptions:
            if send_web_push(subscription, payload):
                user_sent_count += 1
                sent_count += 1

        if user_sent_count:
            ScheduleNotification.objects.create(
                user=user,
                township=township,
                schedule=schedule,
            )

    return {
        "sent_count": sent_count,
        "skipped_no_change_count": skipped_no_change_count,
        "schedule_id": schedule.id,
    }
