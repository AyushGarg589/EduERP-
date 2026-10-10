from django.urls import path
from apps.students.views import (
    StudentListView,
    StudentTableView,
    StudentDetailView,
    StudentUpdateView,
    StudentDeleteView,
    StudentCreateView
)



urlpatterns = [
    path("" , StudentListView.as_view(), name="student_list"),
    path("table/", StudentTableView.as_view(), name="student_table"),

    path("<int:student_id>/" , StudentDetailView.as_view() , name="student_detail"),

    path("<int:student_id>/update/" , StudentUpdateView.as_view() , name="student_update"),

    path("<int:student_id>/delete/" , StudentDeleteView.as_view() , name="student_delete"),
    
    path("add/" , StudentCreateView.as_view() , name="student_add"),
]