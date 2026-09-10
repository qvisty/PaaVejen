from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone")
        labels = {
            "first_name": "Fornavn",
            "last_name": "Efternavn",
            "email": "E-mail",
            "phone": "Telefon",
        }


class SignupForm(UserCreationForm):
    accept_terms = forms.BooleanField(
        label="Jeg har læst og accepterer vilkårene, herunder ansvarsfordelingen "
              "og listen over forbudte genstande.",
        required=True,
    )

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

    def save(self, commit=True):
        from django.utils import timezone

        user = super().save(commit=False)
        user.terms_accepted_at = timezone.now()
        if commit:
            user.save()
        return user
