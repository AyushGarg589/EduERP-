from django.urls import path

from apps.faculty.api_views import (
    FacultyCitiesApi,
    FacultyStatesApi,
)


app_name = "faculty"

urlpatterns = [
    path("states/", FacultyStatesApi.as_view(), name="faculty_states_api"),
    path("cities/", FacultyCitiesApi.as_view(), name="faculty_cities_api"),
]