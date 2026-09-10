from django.urls import path

from . import views

urlpatterns = [
    path("<int:pk>/", views.booking_detail, name="booking_detail"),
    path("<int:pk>/accepter/", views.booking_accept, name="booking_accept"),
    path("<int:pk>/afvis/", views.booking_decline, name="booking_decline"),
    path("<int:pk>/afhentning/", views.booking_pickup, name="booking_pickup"),
    path("<int:pk>/aflevering/", views.booking_deliver, name="booking_deliver"),
]
