from django.contrib import admin
from django.contrib.auth import get_user_model
from django import forms
from django.core.exceptions import ValidationError

from apps.accounts.admin import PlatformAdmin
from apps.faculty.models import (
    Faculty ,
    FacultyContact ,
    FacultyAddress ,
    FacultyQualification ,
)
from apps.institute_app.models import InstituteMembership


class FacultyAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = (
            get_user_model()._default_manager.filter(is_superuser=False)
            .exclude(institute_membership__isnull=False)
            .exclude(faculty_profile__isnull=False)
        )

    class Meta:
        model = Faculty
        exclude = ("institute",)

    def clean(self):
        cleaned_data = super().clean()
        emp_id = cleaned_data.get("emp_id")
        campus = cleaned_data.get("campus")

        if emp_id and campus:
            duplicates = Faculty.objects.filter(
                institute=campus.institute,
                emp_id=emp_id,
            )
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                self.add_error(
                    "emp_id",
                    ValidationError(
                        "This employee ID is already used in this institute.",
                        code="duplicate_emp_id_in_institute",
                    ),
                )

        return cleaned_data

    def clean_user(self):
        user = self.cleaned_data.get("user")
        if user is None:
            return user
        if user.is_superuser or InstituteMembership.objects.filter(user=user).exists():
            raise ValidationError(
                "Select an account that is not a platform superuser or institute owner."
            )
        linked_faculties = Faculty.objects.filter(user=user)
        if self.instance.pk:
            linked_faculties = linked_faculties.exclude(pk=self.instance.pk)
        if linked_faculties.exists():
            raise ValidationError("This account is already linked to another faculty profile.")
        return user


@admin.register(Faculty)
class FacultyAdmin(PlatformAdmin):
    form = FacultyAdminForm

    list_display = (
        "faculty_id",
        "emp_id",
        "full_name",
        "user",
        "campus",
        "employment",
        "joining_date",
        "status",
    )

    search_fields = (
        "emp_id",
        "full_name",
        "user__username",
        "user__email",
        "campus__campus_name",
    )

    list_filter = (
        "campus",
        "employment",
        "gender",
        "status",
    )


@admin.register(FacultyContact)
class FacultyContactAdmin(PlatformAdmin):

    list_display = (
        "contact_id",
        "faculty",
        "email",
        "phone_number",
        "alternate",
    )

    search_fields = (
        "faculty__full_name",
        "faculty__emp_id",
        "email",
        "phone_number",
    )


@admin.register(FacultyAddress)
class FacultyAddressAdmin(PlatformAdmin):

    list_display = (
        "address_id",
        "faculty",
        "city",
        "state",
        "country",
        "pincode",
    )

    search_fields = (
        "faculty__full_name",
        "faculty__emp_id",
        "city",
        "state",
        "pincode",
    )

    list_filter = (
        "city",
        "state",
        "country",
    )


@admin.register(FacultyQualification)
class FacultyQualificationAdmin(PlatformAdmin):

    list_display = (
        "qualification_id",
        "faculty",
        "department",
        "designation",
        "specialization",
        "qualification",
        "experience",
    )

    search_fields = (
        "faculty__full_name",
        "faculty__emp_id",
        "department__department_name",
        "qualification",
        "specialization",
    )

    list_filter = (
        "department",
        "designation",
        "qualification",
    )
