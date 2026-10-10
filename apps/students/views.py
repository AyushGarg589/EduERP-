from django.db.models import Q
from django.shortcuts import get_object_or_404 , redirect , render
from django.views.generic import ListView, DetailView , UpdateView , DeleteView 
from django.urls import reverse_lazy 
from django.contrib import messages
from django.db import transaction
from django.views import View


from apps.students.models import (
    Student,
    StudentContact,
    StudentEnrollment,
    StudentAddress,
    GuardianDetails,
    DocumentDetails,
)
from apps.institute_app.models import Campus, Course, Department
from apps.institute_app.tenancy import InstituteRequiredMixin



class StudentListView(InstituteRequiredMixin, ListView):
    
    model = Student
    template_name = "admin/students/student_list.html"
    context_object_name = "students"
    tenant_lookup = "campus__institute"

    def get_context_data(self, **kwargs):
        # Get the default context from ListView
        context = super().get_context_data(**kwargs)

        # Send courses and departments to the template
        context["courses"] = self.scope_queryset(
            Course.objects.all(),
            "campus__institute",
        )
        context["departments"] = self.scope_queryset(
            Department.objects.all(),
            "campus__institute",
        )

        return context


class StudentTableView(InstituteRequiredMixin, ListView):
    model = Student
    template_name = "admin/students/partials/student_table.html"
    context_object_name = "students"

    paginate_by = 5
    tenant_lookup = "campus__institute"

    def get_queryset(self):

        queryset = self.scope_queryset(
            Student.objects.select_related('contact').prefetch_related(
                'enrollments__course',
                'enrollments__branch',
            ),
            "campus__institute",
        )

        search = self.request.GET.get("search")
        course = self.request.GET.get("course")
        branch = self.request.GET.get("branch")
        status = self.request.GET.get("status")

        
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) | 
                Q(contact__email__icontains=search) |
                Q(student_id__icontains=search)
            )

        if course:
            queryset = queryset.filter(enrollments__course__course_name=course)

        if branch:
            queryset = queryset.filter(enrollments__branch__department_name=branch)

        if status == "active":
            queryset = queryset.filter(status=True)
        elif status == "inactive":
            queryset = queryset.filter(status=False)

        return queryset.distinct().order_by("student_id")



class StudentDetailView(InstituteRequiredMixin, DetailView):
    model = Student
    template_name = "admin/students/student_detail.html"
    context_object_name = "student"
    pk_url_kwarg = "student_id"
    tenant_lookup = "campus__institute"


class StudentUpdateView(InstituteRequiredMixin, UpdateView):
    model = Student
    template_name = "admin/students/update_student.html"
    context_object_name = "student"

    fields = [
        "full_name",
        "date_of_birth",
        "gender",
        "blood_group",
        "profile_photo",
        "campus",
        "status",
    ]

    pk_url_kwarg = "student_id"
    tenant_lookup = "campus__institute"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["campus"].queryset = self.scope_queryset(
            Campus.objects.all(),
            "institute",
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Existing contact
        context["contact"] = getattr(
            self.object,
            "contact",
            None
        )

        # Current enrollment
        context["enrollment"] = (
            self.object.enrollments.first()
        )

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Update Student model
        student_form = self.get_form()

        if not student_form.is_valid():
            return self.form_invalid(student_form)

        enrollment = self.object.enrollments.first()
        campus = student_form.cleaned_data["campus"]
        if enrollment and (
            enrollment.course.campus_id != campus.campus_id
            or enrollment.branch.campus_id != campus.campus_id
        ):
            student_form.add_error(
                "campus",
                "The selected campus must match the student's enrolled course and department.",
            )
            return self.form_invalid(student_form)

        student = student_form.save()

        # Update Student Contact
        contact = getattr(student, "contact", None)

        if contact:
            contact.email = request.POST.get("email", "")
            contact.phone_number = request.POST.get("phone_number", "")
            contact.alternate = request.POST.get("alternate", "")
            contact.save()

        # Update Enrollment
        enrollment = student.enrollments.first()

        if enrollment:
            enrollment.campus = student.campus
            enrollment.academic_year = request.POST.get(
                "academic_year",
                enrollment.academic_year
            )

            enrollment.semester = request.POST.get(
                "semester",
                enrollment.semester
            )

            enrollment.section = request.POST.get(
                "section",
                enrollment.section
            )

            enrollment.roll_no = request.POST.get(
                "roll_no",
                enrollment.roll_no
            )

            enrollment.save()

        messages.success(
            request,
            "Student updated successfully."
        )

        return redirect("student_detail", student_id=student.student_id)



class StudentDeleteView(InstituteRequiredMixin, DeleteView):
    model = Student
    template_name = "admin/students/student_confirm_delete.html"

    pk_url_kwarg = 'student_id'
    success_url = reverse_lazy("student_list")
    tenant_lookup = "campus__institute"


class StudentCreateView(InstituteRequiredMixin, View):

    template_name = "admin/students/add_student.html"

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                campus = self.scope_queryset(
                    Campus.objects.all(),
                    "institute",
                ).filter(pk=request.POST.get("campus")).first()
                if campus is None:
                    raise ValueError("Select a campus belonging to your institute.")

                course = Course.objects.filter(
                    pk=request.POST.get("course"),
                    campus=campus,
                ).first()
                if course is None:
                    raise ValueError("Select a course offered at the selected campus.")

                department = Department.objects.filter(
                    pk=request.POST.get("branch"),
                    campus=campus,
                ).first()
                if department is None or course.department_id != department.department_id:
                    raise ValueError("Select the department linked to the selected course.")

                # -------------------------
                # 1. STUDENT
                # -------------------------
                student = Student.objects.create(
                    full_name=request.POST.get("full_name"),
                    date_of_birth=request.POST.get("date_of_birth"),
                    gender=request.POST.get("gender"),
                    blood_group=request.POST.get("blood_group") or None,
                    campus=campus,
                    profile_photo=request.FILES.get("profile_photo"),
                )

                # -------------------------
                # 2. CONTACT
                # -------------------------
                StudentContact.objects.create(
                    student=student,
                    email=request.POST.get("email"),
                    phone_number=request.POST.get("phone_number"),
                    alternate_phone=request.POST.get("alternate") or None,
                )

                # -------------------------
                # 3. ADDRESS
                # -------------------------
                StudentAddress.objects.create(
                    student=student,
                    address_line=request.POST.get("address_line"),
                    city=request.POST.get("city"),
                    state=request.POST.get("state"),
                    country=request.POST.get("country") or "India",
                    pincode=request.POST.get("pincode"),
                )

                # -------------------------
                # 4. GUARDIAN
                # -------------------------
                GuardianDetails.objects.create(
                    student=student,
                    guardian_name=request.POST.get("guardian_name"),
                    relationship=request.POST.get("relationship"),
                    phone_number=request.POST.get("guardian_phone"),
                    email=request.POST.get("guardian_email"),
                    occupation=request.POST.get("occupation"),
                )

                # -------------------------
                # 5. ENROLLMENT
                # -------------------------
                StudentEnrollment.objects.create(
                    student=student,
                    course=course,
                    branch=department,
                    campus=student.campus,
                    academic_year=request.POST.get("academic_year"),
                    semester=request.POST.get("semester"),
                    section=request.POST.get("section"),
                    roll_no=request.POST.get("roll_no"),
                )

                # -------------------------
                # 6. DOCUMENTS
                # -------------------------
                DocumentDetails.objects.create(
                    student=student,
                    marksheet_10=request.FILES.get("marksheet_10"),
                    marksheet_12=request.FILES.get("marksheet_12"),
                    aadhaar=request.FILES.get("aadhaar"),
                    migration_certificate=request.FILES.get("migration_certificate"),
                    certificate=request.FILES.get("certificate"),
                )


            # Everything saved successfully
            messages.success(
                request,
                "Student admitted successfully."
            )

            return redirect(
                "student_detail",
                student_id=student.student_id
            )

        except Exception as e:

            messages.error(
                request,
                f"Unable to create student: {str(e)}"
            )

            return redirect("student_add")


    def get(self, request, *args, **kwargs):
        context = {
            "campuses": self.scope_queryset(Campus.objects.all(), "institute"),
            "courses": self.scope_queryset(Course.objects.all(), "campus__institute"),
            "departments": self.scope_queryset(
                Department.objects.all(),
                "campus__institute",
            ),
        }

        return render(
            request,
            self.template_name,
            context
        )
