from django.urls import path

from apps.dashboard.views import (
    AccountDetailsView,
    AdminDashboardView,
    CustomPasswordChangeView,
    LogoutRedirectView,
)

app_name = "dashboard"

urlpatterns = [
    path("", AdminDashboardView.as_view(), name="home"),
    path("admin/", AdminDashboardView.as_view(), name="admin_dashboard"),
    path("settings/", AccountDetailsView.as_view(), name="settings"),
    path("settings/password/", CustomPasswordChangeView.as_view(), name="password_change"),
    path("logout/", LogoutRedirectView.as_view(), name="logout_home"),
]
