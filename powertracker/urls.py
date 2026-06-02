from django.urls import path
from . import views

urlpatterns = [
    path('', views.home,name="home"),
    path("townships/<int:township_id>/", views.township_detail, name="township_detail"),

]