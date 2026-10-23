from django.urls import path
from apps.institute_app.views import (
    CampusCreateView,
    CampusDeleteView,
    CampusListView,
    CampusUpdateView,
    CourseListView,
    CourseCreateView,
    CourseUpdateView,
    CourseDeleteView,
    DepartmentCreateView,
    DepartmentDeleteView,
    DepartmentListView,
    DepartmentUpdateView,
    InstituteSetupView,
)

app_name = "institute"

urlpatterns = [
    path('courses/' , CourseListView.as_view() , name="course_list"),
    path('course/add/' , CourseCreateView.as_view() , name='course_add'),
    path('course/<int:course_id>/edit/', CourseUpdateView.as_view(), name='course_edit'),
    path('course/<int:course_id>/delete/', CourseDeleteView.as_view(), name='course_delete'),
    path('setup/institute/', InstituteSetupView.as_view(), name='institute_setup'),
    path('setup/campuses/', CampusListView.as_view(), name='campus_list'),
    path('setup/campuses/add/', CampusCreateView.as_view(), name='campus_add'),
    path('setup/campuses/<int:pk>/edit/', CampusUpdateView.as_view(), name='campus_edit'),
    path('setup/campuses/<int:pk>/delete/', CampusDeleteView.as_view(), name='campus_delete'),
    path('setup/departments/', DepartmentListView.as_view(), name='department_list'),
    path('setup/departments/add/', DepartmentCreateView.as_view(), name='department_add'),
    path('setup/departments/<int:pk>/edit/', DepartmentUpdateView.as_view(), name='department_edit'),
    path('setup/departments/<int:pk>/delete/', DepartmentDeleteView.as_view(), name='department_delete'),
]
