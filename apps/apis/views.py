from django.shortcuts import render
from rest_framework import status 
from rest_framework.views import APIView
from rest_framework.response import Response 
from rest_framework.decorators import api_view , permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.generics import get_object_or_404 , GenericAPIView

from apps.apis.serializers import StudentTestSerializer
from apps.students.serializers import StudentSerializer

from apps.students.models import Student
from apps.institute_app.tenancy import ActiveInstitutePermission, scope_queryset


@api_view(['GET'])
@permission_classes([AllowAny])
def testapi(request):
    return Response({
        "message" : "Hi This is the Test Api for EduERP.."
    })


class HealthCheckApi(APIView):

    permission_classes = [AllowAny]

    def get(self , request):
        return Response({
            "status": "success",
            "message": "EduERP API is healthy"
        } , status=status.HTTP_200_OK)

    def post(self , request):
        return Response({
            "name": f"This is for : {request.data.get('name')}"
        }) 


class StudentCheck(APIView):

    permission_classes = [AllowAny]

    def post(self , request):
        serializer = StudentTestSerializer(data = request.data)
        if serializer.is_valid():
            return Response({
                "message" : "Your Data is successfully Submitted" ,
                "data": serializer.validated_data
            } , status=status.HTTP_201_CREATED)
        return Response({
            "message" : "You sent some Wrong Data Format",
            "errors": serializer.errors
        } , status=status.HTTP_400_BAD_REQUEST)


"""
class StudentListApi(APIView):

    permission_classes = [AllowAny]

    def get(self , request):
        student_data = Student.objects.all()
        serialized_data = StudentSerializer(instance=student_data , many=True) 
        return Response({
            "message" : "This is the Student Data" , 
            "data" : f"{serialized_data.data}"
        } , status=status.HTTP_200_OK)
"""

class StudentListApi(GenericAPIView):
    permission_classes = [IsAuthenticated, ActiveInstitutePermission]

    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get_queryset(self):
        return scope_queryset(
            super().get_queryset(),
            self.request.user,
            "campus__institute",
        )

    def get(self , request):
        student_data = self.get_queryset()
        serializer = self.get_serializer(
            student_data,
            many=True
        )
        return Response({
            "message": "This is the Student Data",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    


class StudentDetailApi(APIView):

    permission_classes = [IsAuthenticated, ActiveInstitutePermission]

    def get(self , request , student_id):
        student_data = get_object_or_404(
            scope_queryset(Student.objects.all(), request.user, "campus__institute"),
            student_id=student_id,
        )
        serialized_data = StudentSerializer(student_data)
        return Response({
            "message" : "Student Found" , 
            "data" : serialized_data.data
        } , status=status.HTTP_200_OK)


class StudentCreateApi(APIView):

    permission_classes = [IsAuthenticated, ActiveInstitutePermission]

    def post(self , request):
        serialized_data = StudentSerializer(
            data=request.data,
            context={"request": request},
        )
        if serialized_data.is_valid():
            serialized_data.save()
            return Response({
                "message" : "Data Added Successfully", 
                "data" : serialized_data.data
            } , status=status.HTTP_201_CREATED)
        return Response({
            "errors" : serialized_data.errors
        } , status=status.HTTP_400_BAD_REQUEST)


class StudentUpdateApi(APIView):
    permission_classes = [IsAuthenticated, ActiveInstitutePermission]

    def put(self , request , student_id):
        student_data = get_object_or_404(
            scope_queryset(Student.objects.all(), request.user, "campus__institute"),
            student_id=student_id,
        )
        serialized_data = StudentSerializer(
            instance=student_data,
            data=request.data,
            context={"request": request},
        )
        if serialized_data.is_valid():
            serialized_data.save()
            return Response({
                "message" : "Update Successfully" , 
                "data" : serialized_data.data
            } , status=status.HTTP_200_OK)
        return Response({
            "message" : "Having Trouble to Save your Data" , 
            "errors" : serialized_data.errors
        } , status=status.HTTP_400_BAD_REQUEST)


class StudentDeleteApi(APIView):

    permission_classes = [IsAuthenticated, ActiveInstitutePermission]

    def delete(self , request , student_id):
        student_data = get_object_or_404(
            scope_queryset(Student.objects.all(), request.user, "campus__institute"),
            student_id=student_id,
        )
        student_data.delete()
        return Response({
            "message" : "Student Data Dumps Successfully"
        }, status=status.HTTP_204_NO_CONTENT)


class StudentPatchApi(APIView):

    permission_classes = [IsAuthenticated, ActiveInstitutePermission]

    def patch(self , request , student_id):

        student_data = get_object_or_404(
            scope_queryset(Student.objects.all(), request.user, "campus__institute"),
            student_id=student_id,
        )
        serialized_data = StudentSerializer(
            instance = student_data,
            data = request.data,
            partial = True,
            context={"request": request},
        )

        if serialized_data.is_valid():
            serialized_data.save()
            return Response({
                "message" : "Data Updated Successfully",
                "data" : serialized_data.data 
            } , status=status.HTTP_200_OK)
        return Response({
            "message" : "Something went Wrong",
            "errors" : serialized_data.errors
        } , status=status.HTTP_400_BAD_REQUEST)

