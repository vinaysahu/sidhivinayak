from django.db import models
from django.utils import timezone


class Amenities(models.Model):
    
    name = models.CharField(max_length=32, unique=True)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Amenity"              # singular name in sidebar and forms
        verbose_name_plural = "Amenities"

    def __str__(self):
        return self.name
