from django.urls import path

from . import views

urlpatterns = [
    path("vapid/", views.vapid_public_key, name="push_vapid"),
    path("subscribe/", views.subscribe, name="push_subscribe"),
    path("unsubscribe/", views.unsubscribe, name="push_unsubscribe"),
]
