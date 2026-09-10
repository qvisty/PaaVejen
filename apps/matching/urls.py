from django.urls import path

from . import views

urlpatterns = [
    path("<int:pk>/forespoerg/", views.send_request, name="match_send_request"),
]
