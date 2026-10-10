from django.contrib import admin
from apps.accounts.admin import PlatformAdmin
from apps.students.models import (
    Student , 
    StudentAddress ,
    DocumentDetails , 
    GuardianDetails , 
    StudentContact , 
    StudentEnrollment
)



@admin.register(Student)
class StudentAdmin(PlatformAdmin):

    list_display = (
        "student_id",
        "full_name",
        "campus",
        "gender",
        "status",
        "created_at",
    )

    # Admin mein student ko naam/campus se search kar sakenge
    search_fields = (
        "full_name",
        "campus__campus_name",
    )

    # Campus aur status ke basis par filter
    list_filter = (
        "campus",
        "gender",
        "status",
    )


@admin.register(StudentAddress)
class StudentAddressAdmin(PlatformAdmin):

    list_display = (
        "address_id",
        "student",
        "city",
        "state",
        "country",
        "pincode",
    )

    search_fields = (
        "student__full_name",
        "city",
        "state",
        "pincode",
    )

    list_filter = (
        "city",
        "state",
        "country",
    )


@admin.register(DocumentDetails)
class DocumentDetailsAdmin(PlatformAdmin):

    list_display = (
        "document_id",
        "student",
        "marksheet_10",
        "marksheet_12",
        "aadhaar",
        "migration_certificate",
        "certificate",
        "uploaded_at",
        "verified",
    )

    search_fields = (
        "student__full_name",
    )

    list_filter = (
        "verified",
        "uploaded_at",
    )


@admin.register(GuardianDetails)
class GuardianDetailsAdmin(PlatformAdmin):

    list_display = (
        "guardian_id",
        "student",
        "guardian_name",
        "relationship",
        "phone_number",
        "email",
        "occupation",
    )

    search_fields = (
        "student__full_name",
        "guardian_name",
        "phone_number",
        "email",
    )

    list_filter = (
        "relationship",
        "occupation",
    )


@admin.register(StudentContact)
class StudentContactAdmin(PlatformAdmin):

    list_display = (
        "contact_id",
        "student",
        "email",
        "phone_number",
        "alternate_phone",
    )

    search_fields = (
        "student__full_name",
        "email",
        "phone_number",
        "alternate_phone",
    )



@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(PlatformAdmin):

    list_display = (
        "enrollment_id",
        "student",
        "course",
        "branch",
        "campus",
        "academic_year",
        "semester",
        "section",
        "roll_no",
    )

    search_fields = (
        "student__full_name",
        "roll_no",
        "academic_year",
    )

    list_filter = (
        "campus",
        "course",
        "branch",
        "academic_year",
        "semester",
        "section",
    )

