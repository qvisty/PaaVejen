from django.urls import path

from . import views

urlpatterns = [
    path("ny/", views.trip_create, name="trip_create"),
    path("<int:pk>/", views.trip_detail, name="trip_detail"),
    path("<int:pk>/rediger/", views.trip_edit, name="trip_edit"),
    path("<int:pk>/annuller/", views.trip_cancel, name="trip_cancel"),
]
