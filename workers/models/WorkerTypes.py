from django.db import models
from django.utils import timezone

# Create your models here.
class WorkerTypes(models.Model):
    name = models.CharField(max_length=255)
    wages = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Worker Type"
        verbose_name_plural = "Worker Types"

    def __str__(self):
        return self.name