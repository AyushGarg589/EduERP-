from rest_framework import serializers


class StudentTestSerializer(serializers.Serializer):
    student_id = serializers.BigIntegerField()
    full_name = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    age = serializers.IntegerField()