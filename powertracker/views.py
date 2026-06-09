import json
from calendar import monthrange
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import get_language
from django.views.decorators.http import require_POST

from .helpers.check_status import (
    get_current_schedule,
    get_expected_status_for_township,
)
from .helpers.mm_time import get_current_myanmar_time
from .helpers.gemini_planner import (
    PlannerBusyError,
    PlannerError,
    PlannerRateLimitError,
    PLANNER_LANGUAGES,
    build_ics_calendar,
    generate_planner,
)
from .helpers.report_window import get_report_window
from .helpers.schedule_timeline import get_active_group_at_time, get_upcoming_24h_points
from .helpers.weekly_timetable import (
    get_weekly_timetable_for_group,
    get_weekly_timetable_for_township,
)
from .models import (
    ContactMessage,
    FavoriteTownship,
    Schedule,
    Township,
    UserProfile,
    UserPushSubscription,
    UserReport,
)

MAX_FAVORITE_TOWNSHIPS = 4


def get_first_favorite_township(user):
    if not user.is_authenticated:
        return None

    profile, created = UserProfile.objects.get_or_create(user=user)

    first_favorite = FavoriteTownship.objects.filter(
        user_profile=profile
    ).select_related("township").order_by("position", "created_at").first()

    if first_favorite:
        return first_favorite.township

    return None


def reorder_favorite_positions(profile):
    favorites = FavoriteTownship.objects.filter(
        user_profile=profile
    ).order_by("position", "created_at")

    for index, favorite in enumerate(favorites, start=1):
        if favorite.position != index:
            favorite.position = index
            favorite.save(update_fields=["position"])


def get_status_for_township_at_time(township, target_datetime):
    schedules = Schedule.objects.filter(
        date__in=[
            target_datetime.date() - timedelta(days=1),
            target_datetime.date(),
        ]
    ).order_by("date", "start_time")
    active_group = get_active_group_at_time(target_datetime, schedules)

    if active_group is None:
        return "UNKNOWN"

    if active_group == "All" or active_group == township.group:
        return "ON"

    return "OFF"


def home(request):
    if request.user.is_authenticated and not request.GET:
        first_favorite_township = get_first_favorite_township(request.user)

        if first_favorite_township:
            return redirect(
                "township_detail",
                township_id=first_favorite_township.id
            )

    townships = Township.objects.all().order_by("name")
    myanmar_now = get_current_myanmar_time()
    month_start = myanmar_now.date().replace(day=1)
    month_end = myanmar_now.date().replace(
        day=monthrange(myanmar_now.year, myanmar_now.month)[1]
    )
    selected_date = myanmar_now.date()
    selected_time = myanmar_now.time().replace(second=0, microsecond=0)
    default_township_id = None

    if request.user.is_authenticated:
        default_favorite = get_first_favorite_township(request.user)

        if default_favorite:
            default_township_id = default_favorite.id

    selected_township_id = request.GET.get("township") or default_township_id

    try:
        selected_township_id = int(selected_township_id)
    except (TypeError, ValueError):
        selected_township_id = None

    try:
        selected_date = datetime.strptime(
            request.GET.get("date", ""),
            "%Y-%m-%d"
        ).date()
    except ValueError:
        selected_date = myanmar_now.date()

    if selected_date < month_start or selected_date > month_end:
        selected_date = myanmar_now.date()

    try:
        selected_time = datetime.strptime(
            request.GET.get("time", ""),
            "%H:%M"
        ).time()
    except ValueError:
        selected_time = myanmar_now.time().replace(second=0, microsecond=0)

    selected_township = None
    selected_status = None
    search_submitted = any(
        field in request.GET
        for field in ["township", "date", "time"]
    )

    if selected_township_id:
        selected_township = Township.objects.filter(id=selected_township_id).first()

    if search_submitted and selected_township:
        target_datetime = timezone.make_aware(
            datetime.combine(selected_date, selected_time)
        )
        selected_status = get_status_for_township_at_time(
            selected_township,
            target_datetime
    )

    township_links = [
        {
            "name": township.name,
            "display_name": township.localized_name,
            "url": reverse("township_detail", args=[township.id]),
            "status": township.current_status,
            "group": township.group,
        }
        for township in townships
    ]

    return render(request, "powertracker/home.html", {
        "townships": townships,
        "township_links": township_links,
        "current_schedule": get_current_schedule(),
        "myanmar_now": myanmar_now,
        "month_start": month_start,
        "month_end": month_end,
        "selected_date": selected_date,
        "selected_time": selected_time,
        "selected_township": selected_township,
        "selected_township_id": selected_township_id,
        "selected_status": selected_status,
        "timeline_points": get_upcoming_24h_points(),
    })


def township_statuses(request):
    townships = Township.objects.all().order_by("name")
    myanmar_now = get_current_myanmar_time()

    return JsonResponse({
        "myanmar_time": myanmar_now.isoformat(),
        "townships": [
            {
                "id": township.id,
                "name": township.name,
                "display_name": township.localized_name,
                "status": township.current_status,
                "updated_at": township.updated_at.isoformat(),
            }
            for township in townships
        ],
    })


@login_required
def push_public_key(request):
    return JsonResponse({
        "public_key": getattr(settings, "VAPID_PUBLIC_KEY", ""),
    })


@login_required
@require_POST
def subscribe_push_notifications(request):
    try:
        subscription = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid subscription data."}, status=400)

    endpoint = subscription.get("endpoint")
    keys = subscription.get("keys", {})
    p256dh = keys.get("p256dh")
    auth = keys.get("auth")

    if not endpoint or not p256dh or not auth:
        return JsonResponse({"error": "Missing subscription data."}, status=400)

    UserPushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            "user": request.user,
            "p256dh": p256dh,
            "auth": auth,
            "is_active": True,
        },
    )

    return JsonResponse({"status": "subscribed"})


def offline(request):
    if request.GET.get("fallback") != "1":
        return redirect("home")

    return render(request, "powertracker/offline.html")


@login_required
def contact_us(request):
    townships = Township.objects.all().order_by("name")
    category_choices = ContactMessage.CATEGORY_CHOICES
    form_data = {}
    errors = {}

    if request.method == "POST":
        form_data = {
            "name": request.POST.get("name", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "category": request.POST.get("category", "").strip(),
            "township": request.POST.get("township", "").strip(),
            "message": request.POST.get("message", "").strip(),
        }

        valid_categories = [choice[0] for choice in category_choices]

        if not form_data["name"]:
            errors["name"] = "Please enter your name."

        if not form_data["email"]:
            errors["email"] = "Please enter your email."
        else:
            try:
                validate_email(form_data["email"])
            except ValidationError:
                errors["email"] = "Please enter a valid email."

        if form_data["category"] not in valid_categories:
            errors["category"] = "Please choose a category."

        if not form_data["message"]:
            errors["message"] = "Please enter your message."

        township = None
        if form_data["township"]:
            township = Township.objects.filter(id=form_data["township"]).first()
            if not township:
                errors["township"] = "Please choose a valid township."

        if not errors:
            ContactMessage.objects.create(
                user=request.user if request.user.is_authenticated else None,
                township=township,
                name=form_data["name"],
                email=form_data["email"],
                category=form_data["category"],
                message=form_data["message"],
            )
            messages.success(request, "Your message has been sent.")
            return redirect("contact_us")

        messages.error(request, "Please check the form and try again.")
    else:
        if request.user.is_authenticated:
            form_data = {
                "name": request.user.username,
                "email": request.user.email,
            }

    return render(request, "powertracker/contact_us.html", {
        "contact_email": getattr(settings, "EMAIL_HOST_USER", ""),
        "category_choices": category_choices,
        "townships": townships,
        "form_data": form_data,
        "errors": errors,
    })


def offline_data(request):
    myanmar_now = get_current_myanmar_time()
    first_favorite = get_first_favorite_township(request.user)

    if first_favorite:
        return JsonResponse({
            "cached_at": myanmar_now.isoformat(),
            "first_favorite": {
                "id": first_favorite.id,
                "name": first_favorite.name,
                "group": first_favorite.group,
                "timetable": get_weekly_timetable_for_township(first_favorite),
            },
            "groups": None,
        })

    group_a_townships = Township.objects.filter(group="A").order_by("name")
    group_b_townships = Township.objects.filter(group="B").order_by("name")

    return JsonResponse({
        "cached_at": myanmar_now.isoformat(),
        "first_favorite": None,
        "groups": {
            "A": {
                "name": "Group A",
                "townships": [
                    township.name
                    for township in group_a_townships
                ],
                "timetable": get_weekly_timetable_for_group("A"),
            },
            "B": {
                "name": "Group B",
                "townships": [
                    township.name
                    for township in group_b_townships
                ],
                "timetable": get_weekly_timetable_for_group("B"),
            },
        },
    })


def service_worker(request):
    response = render(
        request,
        "powertracker/service-worker.js",
        content_type="application/javascript",
    )
    response["Service-Worker-Allowed"] = "/"
    return response


def township_detail(request, township_id):
    township = get_object_or_404(Township, id=township_id)
    is_favorite = False
    current_user_report = None
    current_schedule = get_current_schedule()
    expected_status = get_expected_status_for_township(
        township,
        current_schedule
    )
    window_start, window_end = get_report_window()

    if request.user.is_authenticated:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        is_favorite = profile.favorite_townships.filter(id=township.id).exists()
        current_user_report = UserReport.objects.filter(
            user=request.user,
            township=township,
            window_start=window_start
        ).first()

    return render(request, "powertracker/township_detail.html", {
        "township": township,
        "is_favorite": is_favorite,
        "expected_status": expected_status,
        "current_user_report": current_user_report,
        "report_window_start": window_start,
        "report_window_end": window_end,
        "myanmar_now": get_current_myanmar_time(),
        "weekly_timetable": get_weekly_timetable_for_township(township),
    })


def township_detail_status(request, township_id):
    township = get_object_or_404(Township, id=township_id)
    current_schedule = get_current_schedule()
    expected_status = get_expected_status_for_township(
        township,
        current_schedule
    )
    window_start, window_end = get_report_window()
    current_user_report = None

    if request.user.is_authenticated:
        current_user_report = UserReport.objects.filter(
            user=request.user,
            township=township,
            window_start=window_start
        ).first()

    return JsonResponse({
        "id": township.id,
        "name": township.name,
        "display_name": township.localized_name,
        "expected_status": expected_status,
        "current_status": township.current_status,
        "updated_at": township.updated_at.isoformat(),
        "myanmar_time": get_current_myanmar_time().isoformat(),
        "report_window_start": window_start.isoformat(),
        "report_window_end": window_end.isoformat(),
        "reported_status": (
            current_user_report.reported_status
            if current_user_report
            else None
        ),
    })


@login_required
@require_POST
def submit_township_report(request, township_id):
    township = get_object_or_404(Township, id=township_id)
    reported_status = request.POST.get("reported_status")

    if reported_status not in ["ON", "OFF"]:
        messages.error(request, "Invalid report.")
        return redirect("township_detail", township_id=township.id)

    window_start, window_end = get_report_window()

    UserReport.objects.update_or_create(
        user=request.user,
        township=township,
        window_start=window_start,
        defaults={
            "township_status": township.current_status,
            "reported_status": reported_status,
            "window_end": window_end,
        }
    )

    messages.success(request, "Report saved.")
    return redirect("township_detail", township_id=township.id)


@login_required
def toggle_favorite_township(request, township_id):
    township = get_object_or_404(Township, id=township_id)
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    favorite = FavoriteTownship.objects.filter(
        user_profile=profile,
        township=township
    ).first()

    if favorite:
        favorite.delete()
        reorder_favorite_positions(profile)
    else:
        favorite_count = FavoriteTownship.objects.filter(
            user_profile=profile
        ).count()

        if favorite_count >= MAX_FAVORITE_TOWNSHIPS:
            messages.warning(
                request,
                f"You can only keep {MAX_FAVORITE_TOWNSHIPS} favorite townships."
            )
            return redirect("township_detail", township_id=township.id)

        last_position = FavoriteTownship.objects.filter(
            user_profile=profile
        ).aggregate(max_position=Max("position"))["max_position"] or 0

        FavoriteTownship.objects.create(
            user_profile=profile,
            township=township,
            position=last_position + 1
        )

    return redirect("township_detail", township_id=township.id)


@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    favorite_items = FavoriteTownship.objects.filter(
        user_profile=profile
    ).select_related("township").order_by(
        "position",
        "created_at"
    )

    return render(request, "powertracker/profile.html", {
        "profile": profile,
        "favorite_items": favorite_items,
        "max_favorite_townships": MAX_FAVORITE_TOWNSHIPS,
    })


@login_required
def todo_planner(request):
    townships = Township.objects.all().order_by("name")
    selected_township = get_first_favorite_township(request.user)
    planner_data = None
    planner_json = ""
    form_data = {
        "township": selected_township.id if selected_township else "",
        "language": get_language(),
        "tasks": "",
    }

    if request.method == "POST":
        form_data = {
            "township": request.POST.get("township", "").strip(),
            "language": request.POST.get("language", "").strip() or get_language(),
            "tasks": request.POST.get("tasks", "").strip(),
        }

        selected_township = None

        if form_data["township"].isdigit():
            selected_township = Township.objects.filter(
                id=form_data["township"]
            ).first()

        if not selected_township:
            messages.error(request, "Please choose a township.")
        elif not form_data["tasks"]:
            messages.error(request, "Please enter the tasks you want to plan.")
        else:
            try:
                planner_data = generate_planner(
                    selected_township,
                    form_data["tasks"],
                    form_data["language"],
                )
                planner_json = json.dumps(planner_data)
            except (PlannerBusyError, PlannerRateLimitError, PlannerError) as error:
                messages.error(request, str(error))
            except json.JSONDecodeError:
                messages.error(
                    request,
                    "Gemini returned an invalid plan. Please try again."
                )
            except Exception:
                messages.error(request, "Gemini could not generate a plan. Please try again.")

    return render(request, "powertracker/todo_planner.html", {
        "townships": townships,
        "selected_township": selected_township,
        "planner_languages": PLANNER_LANGUAGES,
        "form_data": form_data,
        "planner_data": planner_data,
        "planner_json": planner_json,
    })


@login_required
@require_POST
def download_todo_planner_ics(request):
    try:
        planner_data = json.loads(request.POST.get("planner_json", ""))
        calendar_content = build_ics_calendar(planner_data)
    except (ValueError, KeyError, json.JSONDecodeError):
        messages.error(request, "Could not create calendar file.")
        return redirect("todo_planner")

    response = HttpResponse(calendar_content, content_type="text/calendar")
    response["Content-Disposition"] = 'attachment; filename="electricity-planner.ics"'

    return response


@login_required
def remove_favorite_township(request, township_id):
    if request.method == "POST":
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        township = get_object_or_404(Township, id=township_id)

        FavoriteTownship.objects.filter(
            user_profile=profile,
            township=township
        ).delete()
        reorder_favorite_positions(profile)

        messages.success(request, f"{township.name} removed from favorites.")

    return redirect("profile")


@login_required
@require_POST
def reorder_favorite_townships(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    try:
        data = json.loads(request.body)
        township_ids = [int(township_id) for township_id in data["township_ids"]]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid favorite order."}, status=400)

    if len(township_ids) > MAX_FAVORITE_TOWNSHIPS:
        return JsonResponse({"error": "Too many favorites."}, status=400)

    if len(township_ids) != len(set(township_ids)):
        return JsonResponse({"error": "Favorite order has duplicates."}, status=400)

    favorite_items = FavoriteTownship.objects.filter(
        user_profile=profile,
        township_id__in=township_ids
    )
    existing_ids = set(favorite_items.values_list("township_id", flat=True))

    if set(township_ids) != existing_ids:
        return JsonResponse({"error": "Favorite list does not match."}, status=400)

    with transaction.atomic():
        for position, township_id in enumerate(township_ids, start=1):
            FavoriteTownship.objects.filter(
                user_profile=profile,
                township_id=township_id
            ).update(position=position)

    return JsonResponse({"success": True})


@login_required
def profile_update_username(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()

        if not username:
            messages.error(request, "Username cannot be empty.")
            return redirect("profile")

        username_exists = User.objects.exclude(id=request.user.id).filter(
            username=username
        ).exists()

        if username_exists:
            messages.error(request, "This username is already taken.")
            return redirect("profile")

        request.user.username = username
        request.user.save(update_fields=["username"])
        messages.success(request, "Username updated.")

    return redirect("profile")
