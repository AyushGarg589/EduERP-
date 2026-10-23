from django.urls import path
from . import views
from apps.faculty.views import accept_faculty_invite

app_name = "public"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path('login/' , views.login_page , name="login_page"),
    path('register/' , views.register , name='register'),
    path('faculty-invite/<str:token>/', accept_faculty_invite, name='faculty_invite_accept'),
]
