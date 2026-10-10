from django.urls import path
from apps.faculty.views import (
    FacultyListView,
    FacultyCreateView,
    FacultyTableView,
    FacultyDetailView,
    FacultyUpdateView
)

urlpatterns = [
    path("" , FacultyListView.as_view() , name="faculty_list"),
    path("table/" , FacultyTableView.as_view() , name="faculty_table"),

    path("<int:faculty_id>/" , FacultyDetailView.as_view() , name="faculty_detail"),

    path("<int:faculty_id>/update/" , FacultyUpdateView.as_view() , name="faculty_update"),

    path("add/" , FacultyCreateView.as_view() , name="faculty_add"),
    
]