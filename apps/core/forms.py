"""Fælles formularhjælpere."""
from django import forms

from .geo import lookup_place


class GeocodeFormMixin(forms.Form):
    """
    Hjælper formularer med stednavne.

    Hvis brugeren har angivet et kendt bynavn og ladet koordinaterne stå
    tomme, udfyldes latitude og longitude automatisk. Ukendte steder
    kræver manuelle koordinater i prototypen.
    """

    geocode_fields: list[tuple[str, str, str]] = []

    def clean(self):
        cleaned = super().clean()
        for name_field, lat_field, lng_field in self.geocode_fields:
            name = cleaned.get(name_field)
            lat = cleaned.get(lat_field)
            lng = cleaned.get(lng_field)
            if lat is None or lng is None:
                point = lookup_place(name or "")
                if point is None:
                    self.add_error(
                        name_field,
                        "Stedet blev ikke genkendt. Angiv koordinater manuelt "
                        "eller brug et kendt bynavn, fx Kolding eller Aabenraa.",
                    )
                else:
                    cleaned[lat_field] = point.lat
                    cleaned[lng_field] = point.lng
        return cleaned
