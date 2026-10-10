from django.views.generic import ListView, CreateView , DetailView , UpdateView
from django.db.models import Q
from django.db import transaction 
from django.shortcuts import render , redirect , get_object_or_404
from django.contrib import messages


from apps.institute_app.models import Campus, Department
from apps.institute_app.tenancy import InstituteRequiredMixin
from apps.faculty.models import (
    Faculty, 
    FacultyContact, 
    FacultyAddress,
    FacultyQualification
    )



class FacultyListView(InstituteRequiredMixin, ListView):
    model = Faculty
    template_name = "admin/faculty/faculty_list.html"
    context_object_name = "faculties"
    paginate_by = 5
    tenant_lookup = "campus__institute"

    def get_queryset(self):
        queryset = self.scope_queryset(
            Faculty.objects.select_related("campus", "contact").prefetch_related(
                "qualification_details__department"
            ),
            "campus__institute",
        )

        search = (self.request.GET.get("search") or "").strip()
        department = self.request.GET.get("department")
        campus = self.request.GET.get("campus")
        status = self.request.GET.get("status")

        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search)
                | Q(emp_id__icontains=search)
                | Q(contact__email__icontains=search)
            )

        if department:
            queryset = queryset.filter(qualification_details__department_id=department)

        if campus:
            queryset = queryset.filter(campus_id=campus)

        if status == "active":
            queryset = queryset.filter(status=True)
        elif status == "inactive":
            queryset = queryset.filter(status=False)

        return queryset.distinct().order_by("faculty_id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["departments"] = self.scope_queryset(
            Department.objects.all(),
            "campus__institute",
        )
        context["campuses"] = self.scope_queryset(Campus.objects.all(), "institute")
        return context


class FacultyTableView(FacultyListView):
    template_name = "admin/faculty/partials/faculty_table.html"


class FacultyDetailView(InstituteRequiredMixin, DetailView):
    model = Faculty
    template_name = "admin/faculty/faculty_detail.html"
    context_object_name = "faculty"
    pk_url_kwarg = "faculty_id"
    tenant_lookup = "campus__institute"


class FacultyCreateView(InstituteRequiredMixin, CreateView):
    template_name = "admin/faculty/add_faculty.html"

    def get(self, request, *args, **kwargs):
        context = {
            "departments": self.scope_queryset(
                Department.objects.all(),
                "campus__institute",
            ),
            "campuses": self.scope_queryset(Campus.objects.all(), "institute"),
        }

        return render(
            request,
            self.template_name,
            context
        )

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                campus_id = request.POST.get("campus")
                if not campus_id:
                    raise ValueError("Campus is required.")
                campus = self.scope_queryset(
                    Campus.objects.all(),
                    "institute",
                ).filter(pk=campus_id).first()
                if campus is None:
                    raise ValueError("Select a campus belonging to your institute.")
                emp_id = (request.POST.get("emp_id") or "").strip()
                if Faculty.objects.filter(
                    institute=campus.institute,
                    emp_id=emp_id,
                ).exists():
                    raise ValueError("This employee ID is already used in this institute.")
                department = self.scope_queryset(
                    Department.objects.all(),
                    "campus__institute",
                ).filter(pk=request.POST.get("department")).first()
                if department is None:
                    raise ValueError("Select a department belonging to your institute.")

                faculty = Faculty.objects.create(
                    campus=campus,
                    emp_id=emp_id,
                    full_name=request.POST.get("full_name", "").strip(),
                    date_of_birth=request.POST.get("date_of_birth"),
                    gender=request.POST.get("gender"),
                    blood_group=request.POST.get("blood_group") or None,
                    profile_photo=request.FILES.get("profile_photo"),
                    joining_date=request.POST.get("joining_date"),
                    employment=request.POST.get("employment"),
                    status=request.POST.get("status") == "1",
                    bio=request.POST.get("bio", "").strip() or None,
                )

                FacultyContact.objects.create(
                    faculty=faculty,
                    email=request.POST.get("email", "").strip(),
                    phone_number=request.POST.get("phone_number", "").strip(),
                    alternate=request.POST.get("alternate", "").strip() or None,
                )

                FacultyAddress.objects.create(
                    faculty=faculty,
                    address=request.POST.get("address", "").strip(),
                    city=request.POST.get("city", "").strip(),
                    state=request.POST.get("state", "").strip(),
                    country=request.POST.get("country", "").strip() or "India",
                    pincode=request.POST.get("pincode", "").strip(),
                )

                FacultyQualification.objects.create(
                    faculty=faculty,
                    department=department,
                    designation=request.POST.get("designation", "").strip(),
                    specialization=request.POST.get("specialization", "").strip() or None,
                    qualification=request.POST.get("qualification", "").strip(),
                    experience=request.POST.get("experience", "").strip() or None,
                )
            return redirect(
                "faculty_detail",
                faculty_id=faculty.faculty_id
            )

        except Exception as err:
            messages.error(
                request,
                f"Unable to Create Faculty: {str(err)}"
            )
            return render(
                request,
                self.template_name,
                {
                    "departments": self.scope_queryset(
                        Department.objects.all(),
                        "campus__institute",
                    ),
                    "campuses": self.scope_queryset(Campus.objects.all(), "institute"),
                }
            )

class FacultyUpdateView(InstituteRequiredMixin, UpdateView):

    model = Faculty
    template_name = "admin/faculty/update_faculty.html"
    context_object_name = "faculty"

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

    pk_url_kwarg = "faculty_id"
    tenant_lookup = "campus__institute"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["departments"] = self.scope_queryset(
            Department.objects.all(),
            "campus__institute",
        )
        context["campuses"] = self.scope_queryset(Campus.objects.all(), "institute")

        context["contact"] = getattr(
            self.object,
            "contact",
            None
        )

        context["address"] = getattr(
            self.object,
            "address",
            None
        )

        context["qualification"] = getattr(
            self.object,
            "qualification_details",
            None
        )

        return context

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()

        form = self.get_form()

        if not form.is_valid():
            return self.form_invalid(form)

        try:
            with transaction.atomic():

                # Update Faculty
                faculty = form.save(commit=False)
                campus_id = request.POST.get("campus")

                if campus_id:
                    campus = self.scope_queryset(
                        Campus.objects.all(),
                        "institute",
                    ).filter(pk=campus_id).first()
                    if campus is None:
                        raise ValueError("Select a campus belonging to your institute.")
                    faculty.campus = campus

                emp_id = (request.POST.get("emp_id") or "").strip()
                if Faculty.objects.filter(
                    institute=faculty.campus.institute,
                    emp_id=emp_id,
                ).exclude(pk=faculty.pk).exists():
                    raise ValueError("This employee ID is already used in this institute.")
                faculty.emp_id = emp_id

                department = self.scope_queryset(
                    Department.objects.all(),
                    "campus__institute",
                ).filter(pk=request.POST.get("department")).first()
                if department is None:
                    raise ValueError("Select a department belonging to your institute.")

                faculty.save()

                # -------------------------
                # Update Contact
                # -------------------------
                contact = getattr(
                    faculty,
                    "contact",
                    None
                )

                if contact is None:
                    contact = FacultyContact.objects.create(
                        faculty=faculty,
                        email=request.POST.get("email", "").strip(),
                        phone_number=request.POST.get("phone_number", "").strip(),
                        alternate=request.POST.get("alternate", "").strip() or None,
                    )
                else:
                    contact.email = request.POST.get("email", "").strip()
                    contact.phone_number = request.POST.get("phone_number", "").strip()
                    contact.alternate = request.POST.get("alternate", "").strip() or None
                    contact.save()

                # -------------------------
                # Update Address
                # -------------------------
                address = getattr(
                    faculty,
                    "address",
                    None
                )

                if address is None:
                    address = FacultyAddress.objects.create(
                        faculty=faculty,
                        address=request.POST.get("address", "").strip(),
                        city=request.POST.get("city", "").strip(),
                        state=request.POST.get("state", "").strip(),
                        country=request.POST.get("country", "").strip() or "India",
                        pincode=request.POST.get("pincode", "").strip(),
                    )
                else:
                    address.address = request.POST.get("address", "").strip()
                    address.city = request.POST.get("city", "").strip()
                    address.state = request.POST.get("state", "").strip()
                    address.country = request.POST.get("country", "").strip() or address.country or "India"
                    address.pincode = request.POST.get("pincode", "").strip()
                    address.save()

                # -------------------------
                # Update Qualification
                # -------------------------
                qualification = getattr(
                    faculty,
                    "qualification_details",
                    None
                )

                if qualification is None:
                    qualification = FacultyQualification.objects.create(
                        faculty=faculty,
                        department=department,
                        designation=request.POST.get("designation", "").strip(),
                        specialization=request.POST.get("specialization", "").strip() or None,
                        qualification=request.POST.get("qualification", "").strip(),
                        experience=request.POST.get("experience", "").strip() or None,
                    )
                else:
                    qualification.department = department
                    qualification.designation = request.POST.get("designation", "").strip()
                    qualification.specialization = request.POST.get("specialization", "").strip() or None
                    qualification.qualification = request.POST.get("qualification", "").strip()
                    qualification.experience = request.POST.get("experience", "").strip() or None
                    qualification.save()

            messages.success(
                request,
                "Faculty updated successfully."
            )

            return redirect(
                "faculty_detail",
                faculty_id=faculty.faculty_id
            )

        except Exception as err:

            messages.error(
                request,
                f"Unable to update faculty: {str(err)}"
            )

            return redirect(
                "faculty_update",
                faculty_id=self.object.faculty_id
            )