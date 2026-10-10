from django.contrib import admin

from .models import RegisterUser


@admin.register(RegisterUser)
class RegisterUserAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "password" , "phone_number")
