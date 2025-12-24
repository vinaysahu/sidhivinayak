from django.db import models
from django.utils import timezone
from .States import States


class Cities(models.Model):
    
    name = models.CharField(max_length=32, unique=True)
    state_id = models.ForeignKey(States, on_delete=models.CASCADE, verbose_name="State")
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "City"              # singular name in sidebar and forms
        verbose_name_plural = "Cities"

    def __str__(self):
        return self.name
