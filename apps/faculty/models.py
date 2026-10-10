from django.conf import settings
from django.db import models
from apps.institute_app.models import Campus, Department, Institute



class Faculty(models.Model):

    # Faculty ki Primary Key
    faculty_id = models.BigAutoField(
        primary_key=True
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="faculty_profile",
        blank=True,
        null=True,
    )

    # Employee ID unique within an institute
    emp_id = models.CharField(
        max_length=50,
    )

    institute = models.ForeignKey(
        Institute,
        on_delete=models.PROTECT,
        related_name="faculty_members",
        editable=False,
    )

    full_name = models.CharField(
        max_length=150
    )

    date_of_birth = models.DateField()


    gender = models.CharField(
        max_length=20
    )


    blood_group = models.CharField(
        max_length=5,
        blank=True,
        null=True
    )

    profile_photo = models.ImageField(
        upload_to="faculty/profile/",
        blank=True,
        null=True
    )


    joining_date = models.DateField()

    # Employment type
    # Example: Permanent, Contract, Visiting
    employment = models.CharField(
        max_length=50
    )

    # Faculty active/inactive
    status = models.BooleanField(
        default=True
    )

    bio = models.TextField(
        blank=True,
        null=True
    )

    # Faculty kis campus mein hai
    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        related_name="faculty"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("institute", "emp_id"),
                name="unique_faculty_emp_id_per_institute",
            )
        ]

    def save(self, *args, **kwargs):
        if self.campus_id:
            self.institute_id = Campus.objects.values_list(
                "institute_id",
                flat=True,
            ).get(pk=self.campus_id)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.emp_id} - {self.full_name}"


"""
===================================================================================================================================
"""


class FacultyContact(models.Model):

    # Contact ki Primary Key
    contact_id = models.BigAutoField(
        primary_key=True
    )

    # Contact kis faculty ka hai
    # Faculty aur Contact ka 1:1 relationship
    faculty = models.OneToOneField(
        Faculty,
        on_delete=models.CASCADE,
        related_name="contact"
    )

    email = models.EmailField()

    # Primary phone number
    phone_number = models.CharField(
        max_length=15
    )

    # Alternate phone number
    alternate = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.faculty.full_name} - Contact"



"""
===================================================================================================================================
"""


class FacultyAddress(models.Model):

    # Faculty address ki Primary Key
    address_id = models.BigAutoField(
        primary_key=True
    )

    # Address kis faculty ka hai
    # Faculty aur Address ka 1:1 relationship
    faculty = models.OneToOneField(
        Faculty,
        on_delete=models.CASCADE,
        related_name="address"
    )

    address = models.CharField(
        max_length=255
    )

    city = models.CharField(
        max_length=100
    )

    state = models.CharField(
        max_length=100
    )

    country = models.CharField(
        max_length=100,
        default="India"
    )

    pincode = models.CharField(
        max_length=10
    )

    def __str__(self):
        return f"{self.faculty.full_name} - Address"



"""
===================================================================================================================================
"""


class FacultyQualification(models.Model):

    # Qualification ki Primary Key
    qualification_id = models.BigAutoField(
        primary_key=True
    )

    # Qualification kis faculty ki hai
    faculty = models.OneToOneField(
        Faculty,
        on_delete=models.CASCADE,
        related_name="qualification_details"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="faculty_qualifications"
    )

    designation = models.CharField(
        max_length=100
    )

    specialization = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    # Highest / relevant qualification
    qualification = models.CharField(
        max_length=150
    )

    experience = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.faculty.full_name} - {self.qualification}"
    


"""
===================================================================================================================================
"""
