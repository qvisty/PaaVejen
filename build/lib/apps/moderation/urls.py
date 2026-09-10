from django.urls import path

from . import views

urlpatterns = [
    path("opgave/<int:request_pk>/", views.report_request, name="report_request"),
]
