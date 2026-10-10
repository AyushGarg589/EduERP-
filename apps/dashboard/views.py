from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.institute_app.tenancy import get_user_institute

@login_required(login_url="public:login_page")
def admin_dashboard(request):
    get_user_institute(request.user)
    return render(request, "admin/admin_dashboard.html")


@require_POST
def logout_home(request):
    logout(request)
    return redirect("public:home")
