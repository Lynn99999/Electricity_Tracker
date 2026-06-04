from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path("townships/<int:township_id>/", views.township_detail, name="township_detail"),
    path(
        "townships/<int:township_id>/favorite/",
        views.toggle_favorite_township,
        name="toggle_favorite_township",
    ),
    path("accounts/profile/", views.profile_view, name="profile"),
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
