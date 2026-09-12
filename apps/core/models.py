from django.db import models


class StoredFile(models.Model):
    """Uploadede filer gemt i databasen.

    På gratis hosting er disken flygtig, mens Postgres er persistent, så
    billeder gemmes her og serveres via et view. Ved skift til ekstern
    objektlagring senere udskiftes alene storagebackenden.
    """

    name = models.CharField(max_length=300, unique=True)
    content = models.BinaryField()
    content_type = models.CharField(max_length=100, default="application/octet-stream")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Gemt fil"
        verbose_name_plural = "Gemte filer"

    def __str__(self):
        return self.name
