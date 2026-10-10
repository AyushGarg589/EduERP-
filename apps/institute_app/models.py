from django.conf import settings
from django.db import models


class Institute(models.Model):

    # Primary Key
    # Django automatically auto-increment karega.
    institute_id = models.BigAutoField(primary_key=True)

    # Institute ka unique code
    # Example: ABC01, IIST01
    institute_code = models.CharField(
        max_length=20,
        unique=True
    )

    # Institute ka full name
    institute_name = models.CharField(
        max_length=150
    )

    # Institute email
    email = models.EmailField(
        blank=True,
        null=True
    )

    # Contact number
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    # Institute ka complete address
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    # Location details
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    state = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    country = models.CharField(
        max_length=100,
        default="India"
    )

    # Postal/PIN code
    pincode = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    # Institute active/inactive status
    status = models.BooleanField(
        default=True
    )

    # Record kab create hua
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        # Admin panel mein institute ka naam show hoga
        return self.institute_name


"""
=================================================================================================================================
"""


class Campus(models.Model):

    # Campus ki primary key
    # Django automatically ID generate karega.
    campus_id = models.BigAutoField(primary_key=True)

    # Har campus kisi ek Institute ke under hoga.
    # on_delete=CASCADE:
    # Agar Institute delete hota hai to uske campuses bhi delete honge.
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name="campuses"
    )

    # Campus ka unique code
    # Example: MAIN, NCR01, CAMP01
    campus_code = models.CharField(
        max_length=20,
        unique=True
    )

    # Campus ka naam
    campus_name = models.CharField(
        max_length=150
    )

    # Campus contact email
    email = models.EmailField(
        blank=True,
        null=True
    )

    # Campus phone number
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    # Campus address
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    # Location details
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    state = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    country = models.CharField(
        max_length=100,
        default="India"
    )

    # Postal/PIN code
    pincode = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    # Campus kab establish hua
    established_year = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    # Campus active/inactive
    status = models.BooleanField(
        default=True
    )

    # Record creation time
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        # Admin panel mein campus ka naam show hoga
        return self.campus_name

"""
=================================================================================================================================
"""

class Department(models.Model):

    # Department ki primary key
    department_id = models.BigAutoField(primary_key=True)

    # Har department ek specific campus ke under hoga
    campus = models.ForeignKey(
        Campus,
        on_delete=models.CASCADE,
        related_name="departments"
    )

    # Department ka unique code
    # Example: CSE, ECE, ME
    department_code = models.CharField(
        max_length=20,
        unique=True
    )

    # Department ka naam
    department_name = models.CharField(
        max_length=150
    )

    # Department kis type ka hai
    # Example: Engineering, Management, Science
    department_type = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # Department ke baare mein short description
    description = models.TextField(
        blank=True,
        null=True
    )

    # Department active/inactive
    status = models.BooleanField(
        default=True
    )

    # Record creation time
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        # Admin panel mein department ka naam show hoga
        return self.department_name


"""
=================================================================================================================================
"""


class Course(models.Model):

    # Course ki primary key
    course_id = models.BigAutoField(primary_key=True)

    # Course kis department ke under hai
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="courses"
    )

    # Course kis campus mein offered hai
    campus = models.ForeignKey(
        Campus,
        on_delete=models.CASCADE,
        related_name="courses"
    )

    # Course ka unique code
    # Example: BTECH-CSE, BCA, MBA
    course_code = models.CharField(
        max_length=30,
        unique=True
    )

    # Course ka naam
    course_name = models.CharField(
        max_length=150
    )

    # Course type
    # Example: UG, PG, Diploma, Certificate
    course_type = models.CharField(
        max_length=50
    )

    # Course ki duration
    # Example: 4 Years, 2 Years
    duration = models.CharField(
        max_length=50
    )

    # Total semesters
    semesters = models.PositiveSmallIntegerField()

    # Total credits
    credits = models.PositiveSmallIntegerField(
        blank=True,
        null=True
    )

    # Course eligibility
    eligibility = models.TextField(
        blank=True,
        null=True
    )

    # Study mode
    # Example: Full Time, Part Time
    study_mode = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    # Course intake/capacity
    intake = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    # Course description
    description = models.TextField(
        blank=True,
        null=True
    )

    # Course ki official website/link
    course_url = models.URLField(
        blank=True,
        null=True
    )

    # Course active/inactive
    status = models.BooleanField(
        default=True
    )

    # Record creation time
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        # Admin panel mein course ka naam show hoga
        return self.course_name


class InstituteMembership(models.Model):
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="institute_membership",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "institute owner"
        verbose_name_plural = "institute owners"

    def __str__(self):
        return f"{self.user} - {self.institute}"

