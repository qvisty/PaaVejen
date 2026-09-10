from django.urls import path

from . import views

urlpatterns = [
    path("booking/<int:booking_pk>/send/", views.send_message, name="message_send"),
]
