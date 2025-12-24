from django.db import models
from django.utils import timezone
from .Countries import Countries


class States(models.Model):
    
    name = models.CharField(max_length=32, unique=True)
    country_id = models.ForeignKey(Countries, on_delete=models.CASCADE, verbose_name="Country")
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "State"              # singular name in sidebar and forms
        verbose_name_plural = "States"

    def __str__(self):
        return self.name
