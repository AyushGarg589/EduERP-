from django import forms

from apps.faculty.models import Faculty


class FacultyUpdateForm(forms.ModelForm):
    # Inactive is a valid value for this select, so false must pass validation.
    status = forms.BooleanField(required=False)

    class Meta:
        model = Faculty
        fields = [
            "emp_id",
            "full_name",
            "date_of_birth",
            "gender",
            "blood_group",
            "profile_photo",
            "joining_date",
            "employment",
            "status",
            "bio",
        ]
