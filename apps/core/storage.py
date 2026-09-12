"""Storagebackend, der gemmer filer i databasen, jf. StoredFile."""
import mimetypes

from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.urls import reverse
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseStorage(Storage):
    def _get_model(self):
        from .models import StoredFile

        return StoredFile

    def _open(self, name, mode="rb"):
        row = self._get_model().objects.get(name=name)
        return ContentFile(bytes(row.content), name=name)

    def _save(self, name, content):
        data = content.read()
        content_type = (
            getattr(content, "content_type", None)
            or mimetypes.guess_type(name)[0]
            or "application/octet-stream"
        )
        self._get_model().objects.create(
            name=name, content=data, content_type=content_type,
        )
        return name

    def exists(self, name):
        return self._get_model().objects.filter(name=name).exists()

    def delete(self, name):
        self._get_model().objects.filter(name=name).delete()

    def size(self, name):
        row = self._get_model().objects.get(name=name)
        return len(bytes(row.content))

    def url(self, name):
        return reverse("stored_file", args=[name])
