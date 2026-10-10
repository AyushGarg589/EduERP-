from django.contrib import admin
from django.contrib.auth import get_user_model

from apps.accounts.admin import PlatformAdmin, PlatformAdminMixin
from apps.institute_app.models import (
    Campus,
    Course,
    Department,
    Institute,
    InstituteMembership,
)



"""
===================================================================================================================================
                                        Admin Site View Points 
===================================================================================================================================
"""


class InstituteMembershipInline(PlatformAdminMixin, admin.TabularInline):
    model = InstituteMembership
    extra = 1
    autocomplete_fields = ("user",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = get_user_model().objects.filter(is_superuser=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Institute)
class InstituteAdmin(PlatformAdmin):
    inlines = (InstituteMembershipInline,)
    list_display = (
        "institute_code",
        "institute_name",
        "status",
        "created_at",
    )


@admin.register(Campus)
class CampusAdmin(PlatformAdmin):
    list_display = (
        "campus_code",
        "campus_name",
        "institute",
        "city",
        "state",
        "status",
    )


@admin.register(Department)
class DepartmentAdmin(PlatformAdmin):

    list_display = (
        "department_code",
        "department_name",
        "campus",
        "department_type",
        "status",
        "created_at",
    )


@admin.register(Course)
class CourseAdmin(PlatformAdmin):

    list_display = (
        "course_code",
        "course_name",
        "department",
        "campus",
        "course_type",
        "duration",
        "semesters",
        "status",
    )
