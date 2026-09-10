from django.contrib.auth.forms import UserCreationForm

from .models import User


class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone")
        labels = {
            "username": "Brugernavn",
            "first_name": "Fornavn",
            "last_name": "Efternavn",
            "email": "E-mail",
            "phone": "Telefon",
        }
