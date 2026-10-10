from django.urls import path , include
from apps.apis.views import (
    testapi ,
    HealthCheckApi,
    StudentCheck,
    StudentListApi,
    StudentDetailApi,
    StudentCreateApi,
    StudentPatchApi,
)


urlpatterns = [
    path('test-api/' , testapi , name='testapi'),
    path('health-check/' , HealthCheckApi.as_view() , name='check-api-health'),
    path('student-api/' , StudentCheck.as_view() , name='student-check-api'),
    path('students/' , StudentListApi.as_view() , name='studentsList'),
    path('student/<int:student_id>/' , StudentDetailApi.as_view() , name='studentDetail'),
    path('add-student/' , StudentCreateApi.as_view() , name='createStudent'),
    path('student/<int:student_id>/patch/' , StudentPatchApi.as_view() , name='studentpartialupdate')
]