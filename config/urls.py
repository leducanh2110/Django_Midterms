from django.contrib import admin
from django.urls import include, path

from accounts import views

urlpatterns = [
    path("", views.home, name="home"),
    path("", include("accounts.urls")),
    path("admin/", admin.site.urls),
]
