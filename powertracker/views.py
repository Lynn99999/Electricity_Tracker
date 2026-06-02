from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .helpers.check_status import get_current_schedule, update_township_statuses
from .helpers.mm_time import get_current_myanmar_time
from .models import Township


def home(request):
    townships = Township.objects.all()
    update_township_statuses()
    township_links = [
        {
            "name": township.name,
            "url": reverse("township_detail", args=[township.id]),
            "status": township.current_status,
        }
        for township in townships
    ]

    return render(request, "powertracker/home.html", {
        "township_links": township_links,
        "current_schedule": get_current_schedule(),
        "myanmar_now": get_current_myanmar_time(),
    })


def township_detail(request, township_id):
    township = get_object_or_404(Township, id=township_id)

    return render(request, "powertracker/township_detail.html", {
        "township": township,
    })