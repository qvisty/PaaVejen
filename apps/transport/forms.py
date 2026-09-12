import io
import pathlib

from django import forms
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from PIL import Image, ImageOps

from apps.core.forms import GeocodeFormMixin

from .models import TransportRequest

# Uploads nedskaleres og genkodes, så databasen holdes lille, og EXIF
# metadata som GPS position fjernes fra brugernes fotos.
MAX_IMAGE_DIMENSION = 1600
JPEG_QUALITY = 82

# Korte forklaringer af opgavetyperne, jf. PRD afsnit 7. Forskellen er,
# hvem der står med varen ved afhentningen.
CATEGORY_DESCRIPTIONS = {
    TransportRequest.Category.BRING_ALONG: (
        "En anden person står klar med varen, fx sælgeren af en stol, "
        "du har købt på DBA. Chaufføren tager den bare med."
    ),
    TransportRequest.Category.PICK_UP: (
        "Chaufføren henter varen i en butik på dine vegne, fx en "
        "Click & Collect ordre, hvor dit ordrenummer skal vises."
    ),
    TransportRequest.Category.DROP_OFF: (
        "Du giver selv varen til chaufføren, som afleverer den ved "
        "destinationen, fx en returnering til en butik."
    ),
}


class TransportRequestForm(GeocodeFormMixin, forms.ModelForm):
    geocode_fields = [
        ("pickup_name", "pickup_lat", "pickup_lng"),
        ("delivery_name", "delivery_lat", "delivery_lng"),
    ]

    class Meta:
        model = TransportRequest
        fields = [
            "category",
            "pickup_name", "pickup_lat", "pickup_lng",
            "delivery_name", "delivery_lat", "delivery_lng",
            "earliest_pickup", "latest_delivery",
            "description", "size", "weight_kg", "estimated_value", "image",
            "terms_accepted",
        ]
        widgets = {
            "earliest_pickup": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M",
            ),
            "latest_delivery": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M",
            ),
            "description": forms.Textarea(attrs={"rows": 3}),
            "pickup_lat": forms.HiddenInput(),
            "pickup_lng": forms.HiddenInput(),
            "delivery_lat": forms.HiddenInput(),
            "delivery_lng": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ("pickup_lat", "pickup_lng", "delivery_lat", "delivery_lng"):
            self.fields[field].required = False
        self.fields["pickup_name"].help_text = "Skriv adressen eller vælg på kortet"
        self.fields["delivery_name"].help_text = "Skriv adressen eller vælg på kortet"
        self.fields["description"].help_text = "Fx: En stol købt på DBA."
        self.fields["terms_accepted"].required = True
        self.fields["terms_accepted"].label = (
            "Jeg bekræfter, at varen ikke er en forbudt genstand, og at "
            "værdien er under 5.000 kr."
        )
        self.fields["terms_accepted"].help_text = "Se vilkårene i sidefoden."

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if not isinstance(image, UploadedFile):
            # Uændret eksisterende billede eller tomt felt.
            return image
        try:
            picture = Image.open(image)
            picture = ImageOps.exif_transpose(picture)
            picture = picture.convert("RGB")
            picture.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))
            buffer = io.BytesIO()
            picture.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        except Exception as error:
            raise forms.ValidationError("Billedet kunne ikke læses.") from error
        stem = pathlib.PurePath(image.name).stem or "billede"
        compressed = ContentFile(buffer.getvalue(), name=f"{stem}.jpg")
        compressed.content_type = "image/jpeg"
        return compressed

    def category_options(self):
        """(værdi, titel, forklaring) for hver opgavetype til skabelonen."""
        return [
            (value, label, CATEGORY_DESCRIPTIONS.get(value, ""))
            for value, label in self.fields["category"].choices
        ]
