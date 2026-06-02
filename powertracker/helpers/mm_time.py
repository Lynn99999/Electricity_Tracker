from django.utils import timezone
from zoneinfo import ZoneInfo

def get_current_myanmar_time():
    return timezone.now().astimezone(ZoneInfo("Asia/Yangon"))
