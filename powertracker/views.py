import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .helpers.check_status import get_current_schedule, update_township_statuses
from .helpers.mm_time import get_current_myanmar_time
from .helpers.schedule_timeline import get_upcoming_24h_points
from .helpers.weekly_timetable import get_weekly_timetable_for_township
from .models import FavoriteTownship, Township, UserProfile

MAX_FAVORITE_TOWNSHIPS = 4


def reorder_favorite_positions(profile):
    favorites = FavoriteTownship.objects.filter(
        user_profile=profile
    ).order_by("position", "created_at")

    for index, favorite in enumerate(favorites, start=1):
        if favorite.position != index:
            favorite.position = index
            favorite.save(update_fields=["position"])


def home(request):
    townships = Township.objects.all()
    # will change to five minutes update later
    # update_township_statuses()
    township_links = [
        {
            "name": township.name,
            "url": reverse("township_detail", args=[township.id]),
            "status": township.current_status,
            "group": township.group,
        }
        for township in townships
    ]

    return render(request, "powertracker/home.html", {
        "township_links": township_links,
        "current_schedule": get_current_schedule(),
        "myanmar_now": get_current_myanmar_time(),
        "timeline_points": get_upcoming_24h_points(),
    })


def township_detail(request, township_id):
    township = get_object_or_404(Township, id=township_id)
    is_favorite = False

    if request.user.is_authenticated:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        is_favorite = profile.favorite_townships.filter(id=township.id).exists()

    return render(request, "powertracker/township_detail.html", {
        "township": township,
        "is_favorite": is_favorite,
        "weekly_timetable": get_weekly_timetable_for_township(township),
    })


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
