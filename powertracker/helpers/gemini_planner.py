import json
import re
import time
from datetime import datetime, timedelta, timezone as datetime_timezone

from django.conf import settings

from powertracker.helpers.mm_time import get_current_myanmar_time
from powertracker.models import Schedule


PLANNING_HOURS = 24
MAX_TASK_TEXT_LENGTH = 1500
MAX_PLANNER_EVENTS = 8
PLANNER_LANGUAGES = {
    "en": "English",
    "my": "Myanmar Burmese",
    "zh-hant": "Traditional Chinese used in Taiwan",
    "zh": "Traditional Chinese used in Taiwan",
}
DEFAULT_PLANNER_LANGUAGE = "en"


class PlannerError(ValueError):
    pass


class PlannerBusyError(PlannerError):
    pass


class PlannerRateLimitError(PlannerError):
    pass


PLANNER_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
        },
        "tips": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                    },
                    "start": {
                        "type": "string",
                    },
                    "end": {
                        "type": "string",
                    },
                    "description": {
                        "type": "string",
                    },
                },
                "required": ["title", "start", "end", "description"],
                "propertyOrdering": ["title", "start", "end", "description"],
            },
        },
    },
    "required": ["summary", "tips", "events"],
    "propertyOrdering": ["summary", "tips", "events"],
}


def schedule_datetime(schedule, schedule_time):
    return datetime.combine(
        schedule.date,
        schedule_time,
        tzinfo=get_current_myanmar_time().tzinfo,
    )


def get_schedule_window(schedule):
    start_datetime = schedule_datetime(schedule, schedule.start_time)
    end_datetime = schedule_datetime(schedule, schedule.end_time)

    if end_datetime <= start_datetime:
        end_datetime += timedelta(days=1)

    return start_datetime, end_datetime


def is_township_on(township, schedule):
    return schedule.active_group == "All" or schedule.active_group == township.group


def get_electricity_on_windows(township, start_datetime=None, hours=PLANNING_HOURS):
    start_datetime = start_datetime or get_current_myanmar_time()
    end_datetime = start_datetime + timedelta(hours=hours)
    schedules = Schedule.objects.filter(
        date__range=(
            start_datetime.date() - timedelta(days=1),
            end_datetime.date(),
        )
    ).order_by("date", "start_time")

    windows = []

    for schedule in schedules:
        if not is_township_on(township, schedule):
            continue

        schedule_start, schedule_end = get_schedule_window(schedule)
        clipped_start = max(schedule_start, start_datetime)
        clipped_end = min(schedule_end, end_datetime)

        if clipped_start >= clipped_end:
            continue

        windows.append({
            "start": clipped_start.replace(second=0, microsecond=0).isoformat(),
            "end": clipped_end.replace(second=0, microsecond=0).isoformat(),
        })

    return windows


def clean_json_response(text):
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    return cleaned


def get_planner_language(language_code):
    return PLANNER_LANGUAGES.get(
        language_code,
        PLANNER_LANGUAGES[DEFAULT_PLANNER_LANGUAGE],
    )


def build_planner_prompt(
    township,
    tasks_text,
    on_windows,
    language_code=DEFAULT_PLANNER_LANGUAGE,
):
    trimmed_tasks = tasks_text[:MAX_TASK_TEXT_LENGTH]
    output_language = get_planner_language(language_code)

    return f"""
You are an efficient time planner for Yangon electricity schedules.

Township: {township.name}
Output language: {output_language}
Electricity ON windows for the next {PLANNING_HOURS} hours:
{json.dumps(on_windows, separators=(",", ":"))}

User tasks:
{trimmed_tasks}

Plan the user's time so electricity-needed tasks are placed inside ON windows first.
Non-electricity tasks may be placed outside ON windows when useful.
Include short breaks when the plan is long.
Do not invent exact task details that the user did not provide.
Return at most {MAX_PLANNER_EVENTS} events.
Write summary, tips, event titles, and event descriptions in {output_language}.
Return only a raw JSON object. Do not include markdown, backticks, or explanatory text outside the JSON.
Ensure events are sorted chronologically by start time.
"""


def get_gemini_status_code(error):
    status_code = getattr(error, "status_code", None)

    if status_code:
        return status_code

    message = str(error)

    if "429" in message:
        return 429

    if "503" in message:
        return 503

    return None


def generate_content(client, prompt):
    last_error = None

    for attempt in range(2):
        try:
            return client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": PLANNER_RESPONSE_SCHEMA,
                    "temperature": 0.2,
                },
            )
        except Exception as error:
            last_error = error
            status_code = get_gemini_status_code(error)

            if status_code == 503 and attempt == 0:
                time.sleep(2)
                continue

            if status_code == 429:
                raise PlannerRateLimitError(
                    "Gemini is rate limited. Please wait a minute and try again."
                ) from error

            if status_code == 503:
                raise PlannerBusyError(
                    "Gemini is busy right now. Please try again in a moment."
                ) from error

            raise

    raise PlannerBusyError(
        "Gemini is busy right now. Please try again in a moment."
    ) from last_error


def generate_planner(
    township,
    tasks_text,
    language_code=DEFAULT_PLANNER_LANGUAGE,
):
    if not settings.GEMINI_API_KEY:
        raise PlannerError("GEMINI_API_KEY is not set.")

    from google import genai

    on_windows = get_electricity_on_windows(township)

    if not on_windows:
        raise PlannerError("No electricity ON windows found for the next 24 hours.")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = generate_content(
        client,
        build_planner_prompt(township, tasks_text, on_windows, language_code),
    )
    planner_data = json.loads(clean_json_response(response.text))

    return normalize_planner_data(planner_data)


def normalize_planner_data(planner_data):
    events = planner_data.get("events", [])
    normalized_events = []

    for event in events:
        title = str(event.get("title", "")).strip()
        start = str(event.get("start", "")).strip()
        end = str(event.get("end", "")).strip()
        description = str(event.get("description", "")).strip()

        if not title or not start or not end:
            continue

        normalized_events.append({
            "title": title,
            "start": start,
            "end": end,
            "description": description,
        })

    normalized_events.sort(key=lambda event: event["start"])

    return {
        "summary": str(planner_data.get("summary", "")).strip(),
        "tips": [
            str(tip).strip()
            for tip in planner_data.get("tips", [])
            if str(tip).strip()
        ],
        "events": normalized_events,
    }


def escape_ics_text(value):
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def parse_event_datetime(value):
    return datetime.fromisoformat(value).astimezone(datetime_timezone.utc)


def format_ics_datetime(value):
    return parse_event_datetime(value).strftime("%Y%m%dT%H%M%SZ")


def build_ics_calendar(planner_data):
    now = datetime.now(datetime_timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Electricity Tracker//Todolist Planner//EN",
        "CALSCALE:GREGORIAN",
    ]

    for index, event in enumerate(planner_data.get("events", []), start=1):
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:electricity-planner-{now}-{index}@electricity-tracker",
            f"DTSTAMP:{now}",
            f"DTSTART:{format_ics_datetime(event['start'])}",
            f"DTEND:{format_ics_datetime(event['end'])}",
            f"SUMMARY:{escape_ics_text(event['title'])}",
            f"DESCRIPTION:{escape_ics_text(event.get('description', ''))}",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")

    return "\r\n".join(lines) + "\r\n"
