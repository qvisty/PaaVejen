from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("oversigt/", views.dashboard, name="dashboard"),
    path("vilkaar/", views.terms, name="terms"),
    path("offline/", views.offline, name="offline"),
]
