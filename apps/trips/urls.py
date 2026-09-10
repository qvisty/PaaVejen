from django.urls import path

from . import views

urlpatterns = [
    path("ny/", views.trip_create, name="trip_create"),
    path("gentagen/ny/", views.recurring_create, name="recurring_create"),
    path("gentagen/<int:pk>/", views.recurring_detail, name="recurring_detail"),
    path("gentagen/<int:pk>/rediger/", views.recurring_edit, name="recurring_edit"),
    path("gentagen/<int:pk>/deaktiver/", views.recurring_deactivate, name="recurring_deactivate"),
    path("<int:pk>/", views.trip_detail, name="trip_detail"),
    path("<int:pk>/rediger/", views.trip_edit, name="trip_edit"),
    path("<int:pk>/annuller/", views.trip_cancel, name="trip_cancel"),
]
