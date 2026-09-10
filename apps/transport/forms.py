from django import forms

from apps.core.forms import GeocodeFormMixin

from .models import TransportRequest


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
            "description", "size", "weight_kg", "estimated_value",
        ]
        widgets = {
            "earliest_pickup": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M",
            ),
            "latest_delivery": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M",
            ),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ("pickup_lat", "pickup_lng", "delivery_lat", "delivery_lng"):
            self.fields[field].required = False
        self.fields["pickup_name"].help_text = "Fx Kolding"
        self.fields["delivery_name"].help_text = "Fx Aabenraa"
        self.fields["description"].help_text = "Fx: En stol købt på DBA."
