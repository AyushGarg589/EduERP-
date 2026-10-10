from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status   

from apps.students.serializers import StudentSerializer
from apps.students.models import Student
from apps.institute_app.tenancy import ActiveInstitutePermission, scope_queryset

class StudentListApi(APIView):
    permission_classes = [ActiveInstitutePermission]

    def get(self , request):
        student_data = scope_queryset(
            Student.objects.all(),
            request.user,
            "campus__institute",
        )
        serialized_data = StudentSerializer(student_data , many=True)
        return Response({
            "data" : serialized_data.data
        } , status=status.HTTP_200_OK)

