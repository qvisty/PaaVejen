from django import forms

from apps.core.forms import GeocodeFormMixin

from .models import RecurringTrip, Trip, WEEKDAY_CHOICES


class TripForm(GeocodeFormMixin, forms.ModelForm):
    geocode_fields = [
        ("origin_name", "origin_lat", "origin_lng"),
        ("destination_name", "destination_lat", "destination_lng"),
    ]

    class Meta:
        model = Trip
        fields = [
            "origin_name", "origin_lat", "origin_lng",
            "destination_name", "destination_lat", "destination_lng",
            "departure_time", "max_detour_minutes", "capacity",
        ]
        widgets = {
            "departure_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M",
            ),
            "origin_lat": forms.HiddenInput(),
            "origin_lng": forms.HiddenInput(),
            "destination_lat": forms.HiddenInput(),
            "destination_lng": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ("origin_lat", "origin_lng", "destination_lat", "destination_lng"):
            self.fields[field].required = False
        self.fields["origin_name"].help_text = "Skriv adressen eller vælg på kortet"
        self.fields["destination_name"].help_text = "Skriv adressen eller vælg på kortet"


class RecurringTripForm(GeocodeFormMixin, forms.ModelForm):
    geocode_fields = [
        ("origin_name", "origin_lat", "origin_lng"),
        ("destination_name", "destination_lat", "destination_lng"),
    ]

    weekdays = forms.TypedMultipleChoiceField(
        label="Ugedage",
        choices=WEEKDAY_CHOICES,
        coerce=int,
        widget=forms.CheckboxSelectMultiple,
        help_text="Hvilke dage kører du turen?",
    )

    class Meta:
        model = RecurringTrip
        fields = [
            "origin_name", "origin_lat", "origin_lng",
            "destination_name", "destination_lat", "destination_lng",
            "weekdays", "departure_time", "max_detour_minutes", "capacity",
        ]
        widgets = {
            "departure_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "origin_lat": forms.HiddenInput(),
            "origin_lng": forms.HiddenInput(),
            "destination_lat": forms.HiddenInput(),
            "destination_lng": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ("origin_lat", "origin_lng", "destination_lat", "destination_lng"):
            self.fields[field].required = False
        self.fields["origin_name"].help_text = "Skriv adressen eller vælg på kortet"
        self.fields["destination_name"].help_text = "Skriv adressen eller vælg på kortet"
