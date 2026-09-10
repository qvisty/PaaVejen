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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ("origin_lat", "origin_lng", "destination_lat", "destination_lng"):
            self.fields[field].required = False
        self.fields["origin_name"].help_text = "Fx Kolding"
        self.fields["destination_name"].help_text = "Fx Sønderborg"


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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ("origin_lat", "origin_lng", "destination_lat", "destination_lng"):
            self.fields[field].required = False
        self.fields["origin_name"].help_text = "Fx Aabenraa"
        self.fields["destination_name"].help_text = "Fx Tønder"
