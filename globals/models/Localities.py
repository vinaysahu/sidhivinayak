from django.db import models
from django.utils import timezone
from .Cities import Cities


class Localities(models.Model):
    
    name = models.CharField(max_length=32, unique=True)
    city_id = models.ForeignKey(Cities, on_delete=models.CASCADE, verbose_name="City")
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Locality"              # singular name in sidebar and forms
        verbose_name_plural = "Localities"

    def __str__(self):
        return self.name
