from django.contrib.auth.hashers import make_password
from django import forms 
from .models import RegisterUser

class RegisterUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = RegisterUser
        fields = ['name', 'email', 'phone_number', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        # Hash password before committing to DB
        user.password = make_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user