from django.shortcuts import render , redirect
from django.contrib.auth.forms import AuthenticationForm 
from django.contrib.auth import login , logout , authenticate, get_user_model
from django.contrib.auth.hashers import make_password , check_password
from .forms import RegisterUserForm
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
            login(request, user)
            return redirect('dashboard:home')

        if username_or_email and password:
            try:
                user_obj = User.objects.get(email=username_or_email)
            except User.DoesNotExist:
                user_obj = None

            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('dashboard:home')

        form.add_error(None, '')

    return render(request, 'public/login_page.html', {'form': form})


def register(request):
    if request.method == 'POST':
        user_details = RegisterUserForm(request.POST)

        if user_details.is_valid():
            password = user_details.cleaned_data['password']
            profile = user_details.save(commit=False)
            profile.password = make_password(password)
            profile.save()
            User.objects.create_user(
                username=user_details.cleaned_data['name'],
                email=user_details.cleaned_data['email'],
                password=password,
            )
            messages.success(request, "Registration successful.")
            return redirect('public:login_page')
    else:
        user_details = RegisterUserForm()

    return render(request, 'public/register.html', {'form': user_details})
