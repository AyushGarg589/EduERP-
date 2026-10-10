from django.urls import path

from apps.dashboard.views import admin_dashboard, logout_home

app_name = "dashboard"

urlpatterns = [
    path("", admin_dashboard, name="home"),
    path("admin/", admin_dashboard, name="admin_dashboard"),
    path("logout/", logout_home, name="logout_home"),
]
