from django.db import models
from django.utils import timezone


class Vehicles(models.Model):
    STATUS_CHOICES = (
        (10, 'Active'),
        (20, 'Inactive'),
        (30, 'Deleted'),
    )
    name = models.CharField(max_length=32)
    reg_number = models.CharField(max_length=50, null=True, blank=True)
    model = models.CharField(max_length=50, null=True, blank=True)
    capacity_tons = models.FloatField(null=True, blank=True)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=10)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Vehicle"              # singular name in sidebar and forms
        verbose_name_plural = "Vehicles"

    def __str__(self):
        return self.name
