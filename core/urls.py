from django.urls import path

from core import views

app_name = "core"

urlpatterns = [
    path("", views.can_i, name="can_i"),
]
