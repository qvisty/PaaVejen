from django.urls import path

from . import views

urlpatterns = [
    path("ny/", views.request_create, name="request_create"),
    path("<int:pk>/", views.request_detail, name="request_detail"),
    path("<int:pk>/rediger/", views.request_edit, name="request_edit"),
    path("<int:pk>/annuller/", views.request_cancel, name="request_cancel"),
]
