from django.db import models
from django.utils import timezone

class Brands(models.Model):
    STATUS_CHOICES = (
        (10, 'Active'),
        (20, 'Inactive'),
        (30, 'Deleted'),
    )
    name = models.CharField(max_length=32, unique=True)
    description = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='images/brands/', null=True, blank=True)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=10)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Brand"              # singular name in sidebar and forms
        verbose_name_plural = "Brands"

    def __str__(self):
        return self.name
