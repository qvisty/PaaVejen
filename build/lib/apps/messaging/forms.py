from django import forms

from .models import Message


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["content"]
        labels = {"content": ""}
        widgets = {
            "content": forms.Textarea(
                attrs={"rows": 2, "placeholder": "Skriv en besked"}
            ),
        }
