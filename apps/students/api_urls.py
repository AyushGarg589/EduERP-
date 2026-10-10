from django.urls import path
from apps.students.api_views import StudentListApi



urlpatterns = [
    path("", StudentListApi.as_view(), name="student_api_list"),
]