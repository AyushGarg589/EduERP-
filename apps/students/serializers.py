from rest_framework import serializers
from apps.institute_app.models import Campus
from apps.institute_app.tenancy import get_user_institute
from apps.students.models import (
    Student ,
    StudentAddress ,
    StudentContact , 
    StudentEnrollment , 
    DocumentDetails , 
    GuardianDetails , 
)


class StudentContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentContact
        fields = [
            "contact_id",
            "email",
            "phone_number",
        ]


class StudentSerializer(serializers.ModelSerializer):

    contact = StudentContactSerializer()
    campus = serializers.PrimaryKeyRelatedField(
        queryset=Campus.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Student
        fields = [
            'student_id',
            'full_name',
            'date_of_birth',
            'gender',
            'status',
            'campus',
            'contact'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            institute = get_user_institute(request.user)
            if institute is not None:
                self.fields["campus"].queryset = Campus.objects.filter(
                    institute=institute
                )

    def validate(self, attrs):
        campus = attrs.get("campus")
        if self.instance is not None and campus is not None:
            for enrollment in self.instance.enrollments.all():
                if (
                    enrollment.course.campus_id != campus.campus_id
                    or enrollment.branch.campus_id != campus.campus_id
                ):
                    raise serializers.ValidationError(
                        {"campus": "Campus must match the student's enrolled course and department."}
                    )
        return attrs

    def create(self , validated_data):
        contact_data = validated_data.pop('contact')

        student = Student.objects.create(**validated_data)

        StudentContact.objects.create(
            student=student , 
            **contact_data
        )
        return student

    def update(self , instance , validated_data):
        contact_data = validated_data.pop("contact" , None)

        for attr , value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if contact_data:
            contact = instance.contact

            for attr, value in contact_data.items():
                setattr(contact, attr, value)

            contact.save()
        return instance
