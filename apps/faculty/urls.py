from django.urls import path
from apps.faculty.views import (
    FacultyListView,
    FacultyCreateView,
    FacultyTableView,
    FacultyDetailView,
    FacultyUpdateView,
    FacultyDeleteView,
    FacultyDashboardView,
    FacultyInviteResendView,
)

urlpatterns = [
    path("portal/", FacultyDashboardView.as_view(), name="portal_home"),
    path("<int:faculty_id>/invite/", FacultyInviteResendView.as_view(), name="faculty_invite_resend"),
    path("" , FacultyListView.as_view() , name="faculty_list"),
    path("table/" , FacultyTableView.as_view() , name="faculty_table"),

    path("<int:faculty_id>/" , FacultyDetailView.as_view() , name="faculty_detail"),

    path("<int:faculty_id>/update/" , FacultyUpdateView.as_view() , name="faculty_update"),

    path("<int:faculty_id>/delete/", FacultyDeleteView.as_view(), name="faculty_delete"),

    path("add/" , FacultyCreateView.as_view() , name="faculty_add"),
    
]
