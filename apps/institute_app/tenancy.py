from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from apps.institute_app.models import InstituteMembership


def get_user_institute(user):
    if not user.is_authenticated:
        raise PermissionDenied

    membership = (
        InstituteMembership.objects.select_related("institute")
        .filter(user=user)
        .first()
    )
    if membership is not None:
        if not membership.institute.status:
            raise PermissionDenied("Your institute is inactive.")
        return membership.institute

    return None


def scope_queryset(queryset, user, institute_lookup):
    institute = get_user_institute(user)
    if institute is None:
        return queryset
    return queryset.filter(**{institute_lookup: institute})


class InstituteRequiredMixin(LoginRequiredMixin):
    login_url = "public:login_page"
    tenant_lookup = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.institute = get_user_institute(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.tenant_lookup is None:
            return queryset
        return scope_queryset(queryset, self.request.user, self.tenant_lookup)

    def scope_queryset(self, queryset, institute_lookup):
        return scope_queryset(queryset, self.request.user, institute_lookup)


class ActiveInstitutePermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        try:
            get_user_institute(request.user)
        except PermissionDenied:
            return False

        return True
