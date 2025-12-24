from django.db import models
from django.utils import timezone


class Countries(models.Model):
    
    name = models.CharField(max_length=32, unique=True)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Country"              # singular name in sidebar and forms
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name
