from django.urls import path

from . import views

urlpatterns = [
    path("booking/<int:booking_pk>/", views.rate_booking, name="rate_booking"),
]
