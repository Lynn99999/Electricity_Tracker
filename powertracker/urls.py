from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path("service-worker.js", views.service_worker, name="service_worker"),
    path("contact/", views.contact_us, name="contact_us"),
    path("offline/", views.offline, name="offline"),
    path("offline-data/", views.offline_data, name="offline_data"),
    path(
        "notifications/public-key/",
        views.push_public_key,
        name="push_public_key",
    ),
    path(
        "notifications/subscribe/",
        views.subscribe_push_notifications,
        name="subscribe_push_notifications",
    ),
    path("statuses/", views.township_statuses, name="township_statuses"),
    path("townships/<int:township_id>/", views.township_detail, name="township_detail"),
    path(
        "townships/<int:township_id>/status/",
        views.township_detail_status,
        name="township_detail_status",
    ),
    path(
        "townships/<int:township_id>/favorite/",
        views.toggle_favorite_township,
        name="toggle_favorite_township",
    ),
    path(
        "townships/<int:township_id>/report/",
        views.submit_township_report,
        name="submit_township_report",
    ),
    path("accounts/profile/", views.profile_view, name="profile"),
    path("accounts/profile/planner/", views.todo_planner, name="todo_planner"),
    path(
        "accounts/profile/planner/download/",
        views.download_todo_planner_ics,
        name="download_todo_planner_ics",
    ),
    path(
        "accounts/profile/favorites/<int:township_id>/remove/",
        views.remove_favorite_township,
        name="remove_favorite_township",
    ),
    path(
        "accounts/profile/favorites/reorder/",
        views.reorder_favorite_townships,
        name="reorder_favorite_townships",
    ),
    path(
        "accounts/profile/update-username/",
        views.profile_update_username,
        name="profile_update_username",
    ),
]
