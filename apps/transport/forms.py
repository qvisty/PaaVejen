from django import forms

from apps.core.forms import GeocodeFormMixin

from .models import TransportRequest

# Korte forklaringer af opgavetyperne, jf. PRD afsnit 7.
CATEGORY_DESCRIPTIONS = {
    TransportRequest.Category.BRING_ALONG: (
        "Varen står klar ét sted og skal bare med til et andet, "
        "fx en stol du har købt på DBA."
    ),
    TransportRequest.Category.PICK_UP: (
        "Chaufføren henter varen for dig hos en butik eller person, "
        "fx en Click & Collect ordre, og kører den hjem til dig."
    ),
    TransportRequest.Category.DROP_OFF: (
        "Du giver chaufføren varen, og den afleveres ved destinationen, "
        "fx en vare der skal returneres til en butik."
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

    def category_options(self):
        """(værdi, titel, forklaring) for hver opgavetype til skabelonen."""
        return [
            (value, label, CATEGORY_DESCRIPTIONS.get(value, ""))
            for value, label in self.fields["category"].choices
        ]
