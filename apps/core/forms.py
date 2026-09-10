"""Fælles formularhjælpere."""
from django import forms

from .geocoding import get_geocoder


class GeocodeFormMixin(forms.Form):
    """
    Hjælper formularer med stednavne.

    Hvis brugeren har ladet koordinaterne stå tomme, slås stednavnet op
    via geocoderen: først kendte danske byer, derefter DAWA, som kan slå
    rigtige adresser op. Kan stedet ikke findes, bedes brugeren angive
    koordinater manuelt.
    """

    geocode_fields: list[tuple[str, str, str]] = []

    def clean(self):
        cleaned = super().clean()
        geocoder = get_geocoder()
        for name_field, lat_field, lng_field in self.geocode_fields:
            name = cleaned.get(name_field)
            lat = cleaned.get(lat_field)
            lng = cleaned.get(lng_field)
            if lat is None or lng is None:
                result = geocoder.geocode(name or "")
                if result is None:
                    self.add_error(
                        name_field,
                        "Stedet blev ikke fundet. Prøv en fuld adresse, "
                        "fx Storegade 12, Aabenraa, eller angiv koordinater manuelt.",
                    )
                else:
                    cleaned[lat_field] = result.point.lat
                    cleaned[lng_field] = result.point.lng
        return cleaned
