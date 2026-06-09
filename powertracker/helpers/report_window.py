from datetime import timedelta

from powertracker.helpers.mm_time import get_current_myanmar_time


def get_report_window(target_time=None):
    myanmar_now = target_time or get_current_myanmar_time()
    window_minute = (myanmar_now.minute // 5) * 5
    window_start = myanmar_now.replace(
        minute=window_minute,
        second=0,
        microsecond=0
    )
    window_end = window_start + timedelta(minutes=5)

    return window_start, window_end
