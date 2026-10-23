from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView , TemplateView
from django.db.models import Q
from django.db import transaction 
from django.shortcuts import render , redirect , get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils import timezone


from apps.institute_app.models import Campus, Department
from apps.institute_app.tenancy import InstituteRequiredMixin , FacultyRequiredMixin
from apps.faculty.models import (
    Faculty, 
    FacultyContact, 
    FacultyAddress,
    FacultyQualification
    )
from apps.faculty.forms import FacultyUpdateForm


FACULTY_INVITE_SALT = "faculty-account-invite-v1"


def _faculty_invite_token(faculty):
    return TimestampSigner(salt=FACULTY_INVITE_SALT).sign(
        f"{faculty.pk}:{faculty.contact.email.strip().lower()}"
    )


def accept_faculty_invite(request, token):
    """Let the invited faculty member create and link their login account."""
    signer = TimestampSigner(salt=FACULTY_INVITE_SALT)
    try:
        payload = signer.unsign(token, max_age=7 * 24 * 60 * 60)
        faculty_id, invited_email = payload.split(":", 1)
        faculty = Faculty.objects.select_related("campus", "campus__institute").get(
            pk=faculty_id,
            contact__email__iexact=invited_email,
            status=True,
        )
    except (BadSignature, SignatureExpired, ValueError, Faculty.DoesNotExist):
        messages.error(request, "This faculty invite is invalid or has expired. Ask your institute to send a new one.")
        return redirect("public:login_page")

    if faculty.user_id:
        messages.info(request, "This faculty profile already has a login account. Please sign in.")
        return redirect("public:login_page")

    if request.method == "POST":
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")
        errors = []
        if password != password_confirm:
            errors.append("The passwords do not match.")
        if not password:
            errors.append("Enter a password.")

        User = get_user_model()
        matching_users = User._default_manager.filter(email__iexact=invited_email)
        if matching_users.count() > 1:
            # Older public signups could create duplicate auth accounts for an
            # email. The signed invite proves access to this mailbox, so create
            # a distinct, unambiguous login for this faculty profile.
            user = None
        else:
            user = matching_users.first()
            if user and (user.is_superuser or hasattr(user, "institute_membership")):
                errors.append("This email is already assigned to an institute owner or platform admin.")
            if user and hasattr(user, "faculty_profile"):
                errors.append("This account is already linked to a faculty profile.")
            if user and not user.has_usable_password():
                errors.append("This account needs help from your institute owner before it can be linked.")

        if user is None:
            username_base = invited_email.split("@", 1)[0][:120] or "faculty"
            username = f"{username_base}-{get_random_string(8)}"
            while User._default_manager.filter(username=username).exists():
                username = f"{username_base}-{get_random_string(8)}"
            user = User(username=username, email=invited_email)

        if user is not None:
            try:
                validate_password(password, user=user)
            except ValidationError as error:
                errors.extend(error.messages)

        if not errors:
            with transaction.atomic():
                user.set_password(password)
                user.is_active = True
                user.save()
                faculty.user = user
                faculty.save(update_fields=["user"])
            messages.success(
                request,
                "Your faculty account is ready. Sign in with your faculty email and the password you just created.",
            )
            return redirect("public:login_page")

        return render(request, "public/faculty_invite_accept.html", {
            "faculty": faculty,
            "token": token,
            "errors": errors,
        })

    return render(request, "public/faculty_invite_accept.html", {
        "faculty": faculty,
        "token": token,
        "errors": [],
    })


# @login_required(login_url="public:login_page")
# def faculty_portal_home(request):
#     faculty = getattr(request.user, "faculty_profile", None)
#     if faculty is None or not faculty.status:
#         raise PermissionDenied("An active linked faculty account is required.")
#     return render(request, "faculty/portal_home.html", {"faculty": faculty})
class FacultyDashboardView(FacultyRequiredMixin, TemplateView):
    template_name = "faculty_views/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faculty = self.request.faculty
        sections = {
            "Basic profile": bool(faculty.full_name and faculty.emp_id and faculty.date_of_birth and faculty.gender),
            "Contact details": hasattr(faculty, "contact") and bool(
                faculty.contact.email and faculty.contact.phone_number
            ),
            "Address": hasattr(faculty, "address") and bool(
                faculty.address.address and faculty.address.city and faculty.address.state
            ),
            "Qualifications": hasattr(faculty, "qualification_details") and bool(
                faculty.qualification_details.qualification
                and faculty.qualification_details.designation
            ),
        }
        completed_sections = sum(sections.values())
        today = timezone.localdate()
        years_at_institute = max(0, today.year - faculty.joining_date.year - (
            (today.month, today.day) < (faculty.joining_date.month, faculty.joining_date.day)
        ))
        qualification = getattr(faculty, "qualification_details", None)
        context.update({
            "faculty": faculty,
            "years_at_institute": years_at_institute,
            "profile_completion": round(completed_sections * 100 / len(sections)),
            "profile_sections": list(sections.items()),
            "department_name": qualification.department.department_name if qualification else "Not assigned",
            "designation": qualification.designation if qualification else "Not assigned",
            "dashboard_chart_data": {
                "sectionLabels": list(sections.keys()),
                "sectionValues": [100 if complete else 0 for complete in sections.values()],
                "completedSections": completed_sections,
                "totalSections": len(sections),
            },
        })
        return context


class FacultyInviteResendView(InstituteRequiredMixin, View):
    def post(self, request, faculty_id):
        faculty = self.scope_queryset(
            Faculty.objects.select_related("campus", "campus__institute", "contact"),
            "campus__institute",
        ).filter(pk=faculty_id).first()
        if faculty is None:
            raise PermissionDenied("This faculty profile does not belong to your institute.")
        if faculty.user_id:
            messages.info(request, "This faculty member already has an account.")
        elif not faculty.status:
            messages.error(request, "Activate this faculty profile before sending an account invite.")
        else:
            invite_url = request.build_absolute_uri(
                reverse("public:faculty_invite_accept", args=[_faculty_invite_token(faculty)])
            )
            try:
                send_mail(
                    subject=f"Set up your {faculty.institute.institute_name} faculty account",
                    message=(
                        f"Hello {faculty.full_name},\n\n"
                        f"Your institute has invited you to EduERP for {faculty.campus.campus_name}.\n"
                        f"Use this link within 7 days to set your password and activate your account:\n{invite_url}\n"
                    ),
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    recipient_list=[faculty.contact.email],
                    fail_silently=False,
                )
                messages.success(request, f"A new invite was sent to {faculty.contact.email}.")
            except Exception:
                messages.error(request, "Invite email could not be sent. Check the email settings and try again.")
        return redirect("faculty_detail", faculty_id=faculty_id)



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
            "course__campus__institute",
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


class FacultyDeleteView(InstituteRequiredMixin, DeleteView):
    model = Faculty
    template_name = "admin/faculty/faculty_confirm_delete.html"
    context_object_name = "faculty"
    pk_url_kwarg = "faculty_id"
    success_url = reverse_lazy("faculty_list")
    tenant_lookup = "campus__institute"


class FacultyCreateView(InstituteRequiredMixin, CreateView):
    template_name = "admin/faculty/add_faculty.html"

    def get(self, request, *args, **kwargs):
        context = {
            "departments": self.scope_queryset(
                Department.objects.all(),
                "course__campus__institute",
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
                    "course__campus__institute",
                ).filter(pk=request.POST.get("department")).first()
                if department is None:
                    raise ValueError("Select a department belonging to your institute.")

                faculty_email = (request.POST.get("email") or "").strip().lower()
                if not faculty_email:
                    raise ValueError("A faculty email is required to send the account invite.")

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
                    email=faculty_email,
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
            invite_url = request.build_absolute_uri(
                reverse("public:faculty_invite_accept", args=[_faculty_invite_token(faculty)])
            )
            try:
                send_mail(
                    subject=f"Set up your {faculty.institute.institute_name} faculty account",
                    message=(
                        f"Hello {faculty.full_name},\n\n"
                        f"Your institute has invited you to EduERP for {faculty.campus.campus_name}.\n"
                        f"Use this link within 7 days to set your password and activate your account:\n{invite_url}\n"
                    ),
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    recipient_list=[faculty_email],
                    fail_silently=False,
                )
                messages.success(request, f"Faculty added and an account invite was sent to {faculty_email}.")
            except Exception:
                messages.warning(
                    request,
                    f"Faculty was added, but the invite email could not be sent to {faculty_email}. Ask the administrator to check email settings and resend the invite.",
                )
            return redirect("faculty_detail", faculty_id=faculty.faculty_id)

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
                        "course__campus__institute",
                    ),
                    "campuses": self.scope_queryset(Campus.objects.all(), "institute"),
                }
            )

class FacultyUpdateView(InstituteRequiredMixin, UpdateView):

    model = Faculty
    form_class = FacultyUpdateForm
    template_name = "admin/faculty/update_faculty.html"
    context_object_name = "faculty"

    pk_url_kwarg = "faculty_id"
    tenant_lookup = "campus__institute"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["departments"] = self.scope_queryset(
            Department.objects.all(),
            "course__campus__institute",
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
                # Read the select's explicit values directly. This keeps the
                # status independent of ModelForm checkbox/boolean coercion.
                status_value = request.POST.get("status")
                if status_value not in {"0", "1"}:
                    raise ValueError("Select Active or Inactive for faculty status.")
                faculty.status = status_value == "1"
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
                    "course__campus__institute",
                ).filter(pk=request.POST.get("department")).first()
                if department is None:
                    raise ValueError("Select a department belonging to your institute.")

                faculty.save()
                # Persist the submitted value explicitly as the form also
                # contains several non-model related fields.
                Faculty.objects.filter(pk=faculty.pk).update(
                    status=status_value == "1"
                )

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



            
