from django.db import models
from django.contrib.auth.models import User 

try:
    from phonenumber_field.modelfields import PhoneNumberField
except ImportError:  # pragma: no cover
    PhoneNumberField = None

# Create your models here.

class RegisterUser(models.Model):
    name = models.CharField(max_length=25)
    email = models.EmailField()
    if PhoneNumberField is not None:
        phone_number = PhoneNumberField(unique=True, region="IN")
    else:
        phone_number = models.CharField(max_length=20)
    password = models.CharField()

    def __str__(self):
        return self.name