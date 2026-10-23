from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.db.models import Q
from django.urls import reverse_lazy


from apps.institute_app.models import Campus, Course, Department, Institute
from apps.institute_app.tenancy import (
    InstituteOwnerOrSuperuserRequiredMixin,
    InstituteOwnerRequiredMixin,
)


class CourseListView(InstituteOwnerOrSuperuserRequiredMixin, ListView):
    model = Course
    template_name = "admin/institute/course.html"
    context_object_name = "courses"
    tenant_lookup = "campus__institute"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related("campus").prefetch_related("departments")
        search = self.request.GET.get("search", "").strip()
        campus = self.request.GET.get("campus", "").strip()
        status = self.request.GET.get("status", "").strip()
        course_type = self.request.GET.get("type", "").strip()

        if search:
            queryset = queryset.filter(
                Q(course_name__icontains=search)
                | Q(departments__department_code__icontains=search)
                | Q(departments__department_name__icontains=search)
            )
        if campus:
            queryset = queryset.filter(campus_id=campus)
        if status in {"active", "inactive"}:
            queryset = queryset.filter(status=(status == "active"))
        if course_type:
            queryset = queryset.filter(course_type=course_type)
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_courses = super().get_queryset()
        context["total_courses"] = all_courses.count()
        context["active_courses"] = all_courses.filter(status=True).count()
        context["inactive_courses"] = all_courses.filter(status=False).count()
        context["campuses"] = self.scope_queryset(
            Campus.objects.all(), "institute"
        ).order_by("campus_name").values("campus_id", "campus_name")
        context["course_types"] = all_courses.order_by("course_type").values_list(
            "course_type", flat=True
        ).distinct()
        return context


"""====================================== HELPER FUNCTION (DRY Principle) ==================================================="""
class CourseCampusFormMixin:
    fields = [
        "campus", "course_code", "course_name", "course_type", "duration",
        "semesters", "credits", "eligibility", "study_mode", "intake",
        "description", "course_url", "status",
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["campuses"] = self.scope_queryset(
            Campus.objects.all(), "institute"
        ).order_by("campus_name")
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["campus"].queryset = self.scope_queryset(
            Campus.objects.all(), "institute"
        ).order_by("campus_name")
        return form


class CourseCreateView(
    InstituteOwnerOrSuperuserRequiredMixin, CourseCampusFormMixin, CreateView
):
    model = Course 
    template_name = "admin/institute/add_course.html"
    tenant_lookup = "campus__institute"
    success_url = reverse_lazy("institute:course_list")


class CourseUpdateView(
    InstituteOwnerOrSuperuserRequiredMixin, CourseCampusFormMixin, UpdateView
):
    model = Course
    template_name = "admin/institute/add_course.html"
    tenant_lookup = "campus__institute"
    pk_url_kwarg = "course_id"
    success_url = reverse_lazy("institute:course_list")


class CourseDeleteView(InstituteOwnerOrSuperuserRequiredMixin, DeleteView):
    model = Course
    template_name = "admin/institute/course_confirm_delete.html"
    tenant_lookup = "campus__institute"
    pk_url_kwarg = "course_id"
    success_url = reverse_lazy("institute:course_list")


class InstituteSetupView(InstituteOwnerRequiredMixin, UpdateView):
    model = Institute
    template_name = "admin/institute/institute_setup.html"
    fields = ["institute_name", "email", "phone", "address", "city", "state", "country", "pincode"]
    success_url = reverse_lazy("institute:institute_setup")
    setup_title = "Institute Details"
    setup_description = "Update your institute's contact and location details."

    def get_object(self, queryset=None):
        return self.institute

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["setup_title"] = self.setup_title
        context["setup_description"] = self.setup_description
        return context


class SetupPageContextMixin:
    setup_title = "Institute Setup"
    setup_description = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["setup_title"] = self.setup_title
        context["setup_description"] = self.setup_description
        return context


class CampusListView(InstituteOwnerRequiredMixin, SetupPageContextMixin, ListView):
    model = Campus
    template_name = "admin/institute/campus.html"
    context_object_name = "campuses"
    tenant_lookup = "institute"
    setup_title = "Campuses"
    setup_description = "Manage the campuses that belong to your institute."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campuses = super().get_queryset()
        context["total_campuses"] = campuses.count()
        context["active_campuses"] = campuses.filter(status=True).count()
        context["inactive_campuses"] = campuses.filter(status=False).count()
        return context


class CampusCreateView(InstituteOwnerRequiredMixin, SetupPageContextMixin, CreateView):
    model = Campus
    template_name = "admin/institute/campus_form.html"
    fields = [
        "campus_code", "campus_name", "email", "phone", "address", "city",
        "state", "country", "pincode", "established_year", "status",
    ]
    success_url = reverse_lazy("institute:campus_list")
    setup_title = "Add Campus"
    setup_description = "Add a campus to your institute."

    def form_valid(self, form):
        form.instance.institute = self.institute
        return super().form_valid(form)


class CampusUpdateView(InstituteOwnerRequiredMixin, SetupPageContextMixin, UpdateView):
    model = Campus
    template_name = "admin/institute/campus_form.html"
    fields = [
        "campus_code", "campus_name", "email", "phone", "address", "city",
        "state", "country", "pincode", "established_year", "status",
    ]
    success_url = reverse_lazy("institute:campus_list")
    tenant_lookup = "institute"
    setup_title = "Update Campus"
    setup_description = "Update campus information."


class CampusDeleteView(InstituteOwnerRequiredMixin, SetupPageContextMixin, DeleteView):
    model = Campus
    template_name = "admin/institute/campus_confirm_delete.html"
    success_url = reverse_lazy("institute:campus_list")
    tenant_lookup = "institute"
    setup_title = "Delete Campus"


class DepartmentListView(InstituteOwnerRequiredMixin, SetupPageContextMixin, ListView):
    model = Department
    template_name = "admin/institute/department.html"
    context_object_name = "departments"
    paginate_by = 10
    tenant_lookup = "course__campus__institute"
    setup_title = "Departments"
    setup_description = "Manage departments and the courses they belong to."


    def get_queryset(self):
        return super().get_queryset().select_related("course", "course__campus")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        departments = super().get_queryset()
        context["total_departments"] = departments.count()
        context["active_departments"] = departments.filter(status=True).count()
        context["inactive_departments"] = departments.filter(status=False).count()
        return context


class DepartmentFormMixin:
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["course"].queryset = Course.objects.filter(
            campus__institute=self.institute
        ).select_related("campus")
        return form


class DepartmentCreateView(
    InstituteOwnerRequiredMixin, SetupPageContextMixin, DepartmentFormMixin, CreateView
):
    model = Department
    template_name = "admin/institute/department_form.html"
    fields = ["course", "department_code", "department_name", "department_type", "description", "status"]
    success_url = reverse_lazy("institute:department_list")
    setup_title = "Add Department"
    setup_description = "Choose the course this department belongs to."


class DepartmentUpdateView(
    InstituteOwnerRequiredMixin, SetupPageContextMixin, DepartmentFormMixin, UpdateView
):
    model = Department
    template_name = "admin/institute/department_form.html"
    fields = ["course", "department_code", "department_name", "department_type", "description", "status"]
    success_url = reverse_lazy("institute:department_list")
    tenant_lookup = "course__campus__institute"
    setup_title = "Update Department"
    setup_description = "Update department details and its course assignment."


class DepartmentDeleteView(InstituteOwnerRequiredMixin, SetupPageContextMixin, DeleteView):
    model = Department
    template_name = "admin/institute/department_confirm_delete.html"
    success_url = reverse_lazy("institute:department_list")
    tenant_lookup = "course__campus__institute"
    setup_title = "Delete Department"
