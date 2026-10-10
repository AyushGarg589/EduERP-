from django.db import models
from apps.institute_app.models import Campus , Course , Department




class Student(models.Model):

    # Student ki Primary Key
    # Django automatically auto-increment karega.
    student_id = models.BigAutoField(primary_key=True)

    # Student kis campus se belong karta hai
    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        related_name="students"
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
        upload_to="students/profile/",
        blank=True,
        null=True
    )

    # Student active hai ya inactive
    status = models.BooleanField(
        default=True
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Student record kab last update hua
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.full_name


"""
=================================================================================================================================
"""



class StudentAddress(models.Model):

    # Address ki Primary Key
    address_id = models.BigAutoField(
        primary_key=True
    )

    # Har student ka ek address
    # OneToOneField = 1:1 relationship
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="address"
    )

    # Student complete address
    address_line = models.CharField(
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
        return f"{self.student.full_name} - Address"


"""
=================================================================================================================================
"""


class DocumentDetails(models.Model):

    # Primary Key
    document_id = models.BigAutoField(
        primary_key=True
    )

    # Document kis student ka hai
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="documents"
    )

   
    marksheet_10 = models.FileField(
        upload_to="students/documents/marksheets/10th/",
        blank=True,
        null=True
    )

    
    marksheet_12 = models.FileField(
        upload_to="students/documents/marksheets/12th/",
        blank=True,
        null=True
    )

   
    aadhaar = models.FileField(
        upload_to="students/documents/aadhaar/",
        blank=True,
        null=True
    )

    # Migration Certificate
    migration_certificate = models.FileField(
        upload_to="students/documents/other/",
        blank=True,
        null=True
    )

    # Other Certificate
    certificate = models.FileField(
        upload_to="students/documents/certificates/",
        blank=True,
        null=True
    )


    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )


    verified = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.student.full_name} - Documents"


"""
=================================================================================================================================
"""

class GuardianDetails(models.Model):

    # Guardian ki Primary Key
    guardian_id = models.BigAutoField(
        primary_key=True
    )

    # Guardian kis student ka hai
    # Student aur Guardian ka 1:1 relationship
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="guardian"
    )

    guardian_name = models.CharField(
        max_length=150
    )

    # Student se relationship
    # Example: Father, Mother, Guardian
    relationship = models.CharField(
        max_length=50
    )

    # Guardian ka phone number
    phone_number = models.CharField(
        max_length=15
    )

    # Guardian email
    email = models.EmailField(
        blank=True,
        null=True
    )

    occupation = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.guardian_name} - {self.student.full_name}"


"""
=================================================================================================================================
"""


class StudentContact(models.Model):

    # Contact ki Primary Key
    contact_id = models.BigAutoField(
        primary_key=True
    )

    # Contact kis student ka hai
    # Student aur Contact ka 1:1 relationship
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="contact"
    )

    # Student ka email
    email = models.EmailField()

    # Primary phone number
    phone_number = models.CharField(
        max_length=10
    )

    # Alternate phone number
    alternate_phone = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.student.full_name} - Contact"


"""
=================================================================================================================================
"""


class StudentEnrollment(models.Model):

    # Enrollment ki Primary Key
    enrollment_id = models.BigAutoField(
        primary_key=True
    )

    # Student jiski enrollment hai
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )

    # Student kis course mein enrolled hai
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="student_enrollments"
    )

    # Branch / Department
    branch = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="student_enrollments"
    )

    # Student kis campus mein enrolled hai
    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        related_name="student_enrollments"
    )

    # Academic year
    # Example: 2026-27
    academic_year = models.CharField(
        max_length=20
    )

    # Semester number
    semester = models.PositiveSmallIntegerField()

    # Section
    # Example: A, B, C
    section = models.CharField(
        max_length=20
    )

    # Student ka roll number
    roll_no = models.CharField(
        max_length=30
    )

    def __str__(self):
        return f"{self.student.full_name} - {self.academic_year} - Sem {self.semester}"


