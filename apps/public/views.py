from django.shortcuts import render , redirect
from django.contrib.auth.forms import AuthenticationForm 
from django.contrib.auth import login , logout , authenticate, get_user_model
from django.contrib import messages
from django.views.decorators.cache import cache_page

User = get_user_model()
# Create your views here.

def home(request):
    return render(request, "public/home.html")


def about(request):
    return render(request, "public/about.html")


def contact(request):
    return render(request, "public/contact.html")

def login_page(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')

        if form.is_valid():
            user = form.get_user()
            if hasattr(user, "faculty_profile") and not user.faculty_profile.status:
                form.add_error(None, "Your faculty profile is inactive. Please contact your institute.")
                return render(request, 'public/login_page.html', {'form': form})
            login(request, user)
            return redirect('portal_home' if hasattr(user, "faculty_profile") else 'dashboard:home')

        if username_or_email and password:
            matching_email_users = User.objects.filter(email__iexact=username_or_email)
            faculty_accounts = matching_email_users.filter(faculty_profile__isnull=False).distinct()
            if faculty_accounts.count() == 1:
                user_obj = faculty_accounts.first()
            elif faculty_accounts.count() > 1 or matching_email_users.count() > 1:
                form.add_error(
                    None,
                    "This email is linked to more than one account. Please contact your institute owner.",
                )
                return render(request, 'public/login_page.html', {'form': form})
            else:
                user_obj = matching_email_users.first()

            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)
                if user is not None:
                    if hasattr(user, "faculty_profile") and not user.faculty_profile.status:
                        form.add_error(None, "Your faculty profile is inactive. Please contact your institute.")
                        return render(request, 'public/login_page.html', {'form': form})
                    login(request, user)
                    return redirect('portal_home' if hasattr(user, "faculty_profile") else 'dashboard:home')

        form.add_error(None, '')

    return render(request, 'public/login_page.html', {'form': form})


def register(request):
    messages.info(request, "EduERP accounts are created through an institute invite. Ask your institute owner to invite you.")
    return redirect('public:login_page')
