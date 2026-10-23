from datetime import date

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, UpdateView

from apps.faculty.models import Faculty, FacultyQualification
from apps.institute_app.models import Course
from apps.institute_app.tenancy import get_user_institute
from apps.students.models import DocumentDetails, Student, StudentEnrollment


class AccountDetailsForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ("username", "email")

    def clean_username(self):
        username = self.cleaned_data["username"]
        users = get_user_model()._default_manager.filter(username=username)
        if self.instance.pk:
            users = users.exclude(pk=self.instance.pk)
        if users.exists():
            raise forms.ValidationError("This username is already taken.")
        return username


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "admin/admin_dashboard.html"
    login_url = "public:login_page"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.institute = get_user_institute(request.user)
            if self.institute is None and not request.user.is_superuser:
                raise PermissionDenied("An institute owner account is required.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        institute = self.institute
        students = Student.objects.all()
        faculty = Faculty.objects.all()
        courses = Course.objects.all()
        documents = DocumentDetails.objects.all()
        enrollments = StudentEnrollment.objects.filter(student__status=True)

        if institute is not None:
            students = students.filter(campus__institute=institute)
            faculty = faculty.filter(institute=institute)
            courses = courses.filter(campus__institute=institute)
            documents = documents.filter(student__campus__institute=institute)
            enrollments = enrollments.filter(campus__institute=institute)

        today = timezone.localdate()
        current_month = today.month
        current_year = today.year
        month_keys = []
        for offset in range(5, -1, -1):
            month_index = current_year * 12 + current_month - 1 - offset
            year, zero_based_month = divmod(month_index, 12)
            month_keys.append((year, zero_based_month + 1))
        first_year, first_month = month_keys[0]
        first_month_start = today.replace(year=first_year, month=first_month, day=1)

        monthly_records = {
            (item["month"].year, item["month"].month): item["total"]
            for item in students.filter(created_at__date__gte=first_month_start, created_at__date__lte=today)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Count("student_id"))
        }
        monthly_labels = [date(year, month, 1).strftime("%b %Y") for year, month in month_keys]
        monthly_counts = [monthly_records.get(key, 0) for key in month_keys]

        department_rows = list(
            enrollments.values("branch__department_name")
            .annotate(total=Count("student_id", distinct=True))
            .order_by("-total", "branch__department_name")
        )
        department_labels = [row["branch__department_name"] or "Unassigned" for row in department_rows[:7]]
        department_counts = [row["total"] for row in department_rows[:7]]
        if len(department_rows) > 7:
            department_labels.append("Other")
            department_counts.append(sum(row["total"] for row in department_rows[7:]))

        campus_rows = list(
            students.filter(status=True)
            .values("campus__campus_name")
            .annotate(total=Count("student_id"))
            .order_by("-total", "campus__campus_name")
        )
        campus_labels = [row["campus__campus_name"] for row in campus_rows[:7]]
        campus_counts = [row["total"] for row in campus_rows[:7]]
        if len(campus_rows) > 7:
            campus_labels.append("Other")
            campus_counts.append(sum(row["total"] for row in campus_rows[7:]))

        faculty_department_rows = list(
            FacultyQualification.objects.filter(faculty__in=faculty.filter(status=True))
            .values("department__department_name")
            .annotate(total=Count("faculty_id"))
            .order_by("-total", "department__department_name")
        )
        faculty_department_labels = [
            row["department__department_name"] for row in faculty_department_rows[:7]
        ]
        faculty_department_counts = [row["total"] for row in faculty_department_rows[:7]]
        if len(faculty_department_rows) > 7:
            faculty_department_labels.append("Other")
            faculty_department_counts.append(sum(row["total"] for row in faculty_department_rows[7:]))

        active_student_count = students.filter(status=True).count()
        active_faculty_count = faculty.filter(status=True).count()
        new_student_records_this_month = students.filter(
            created_at__year=today.year,
            created_at__month=today.month,
        ).count()
        active_courses = courses.filter(status=True)
        intake_capacity = active_courses.aggregate(total=Sum("intake"))["total"]

        context.update({
            "total_students": active_student_count,
            "total_faculty": active_faculty_count,
            "student_faculty_ratio": (
                f"{round(active_student_count / active_faculty_count, 1):g}:1"
                if active_faculty_count
                else "N/A"
            ),
            "intake_capacity": intake_capacity if intake_capacity is not None else "Not set",
            "new_student_records_this_month": new_student_records_this_month,
            "pending_documents": documents.filter(verified=False).count(),
            "department_labels": department_labels,
            "department_counts": department_counts,
            "monthly_labels": monthly_labels,
            "monthly_counts": monthly_counts,
            "campus_labels": campus_labels,
            "campus_counts": campus_counts,
            "faculty_department_labels": faculty_department_labels,
            "faculty_department_counts": faculty_department_counts,
            "dashboard_chart_data": {
                "departmentLabels": department_labels,
                "departmentCounts": department_counts,
                "monthlyLabels": monthly_labels,
                "monthlyCounts": monthly_counts,
                "campusLabels": campus_labels,
                "campusCounts": campus_counts,
                "facultyDepartmentLabels": faculty_department_labels,
                "facultyDepartmentCounts": faculty_department_counts,
            },
        })
        return context


class AccountDetailsView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = get_user_model()
    form_class = AccountDetailsForm
    template_name = "dashboard/settings.html"
    success_url = reverse_lazy("dashboard:settings")
    success_message = "Your account details have been updated."
    login_url = "public:login_page"

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account_details_form"] = context.pop("form")
        context["password_change_form"] = PasswordChangeForm(user=self.request.user)
        return context

class CustomPasswordChangeView(PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = "dashboard/settings.html"
    success_url = reverse_lazy("dashboard:settings")
    login_url = "public:login_page"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account_details_form"] = AccountDetailsForm(instance=self.request.user)
        context["password_change_form"] = context.pop("form")
        return context

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed.")
        return super().form_valid(form)

class LogoutRedirectView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect("public:home")

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)
