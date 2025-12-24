from django.db import models
from django.utils import timezone
from .Brands import Brands
from django.core.validators import RegexValidator

class Suppliers(models.Model):
    STATUS_CHOICES = (
        (10, 'Active'),
        (20, 'Inactive'),
        (30, 'Deleted'),
    )
    brand_id = models.ForeignKey(Brands, on_delete=models.CASCADE, verbose_name="Brand", null=True, blank=True)
    shop_name = models.CharField(max_length=32, unique=True)
    logo = models.ImageField(upload_to='images/suppliers/', null=True, blank=True)
    first_name = models.CharField(max_length=32, null=True, blank=True)
    last_name = models.CharField(max_length=32, null=True, blank=True)
    address = models.CharField(max_length=100, null=True, blank=True)
    mobile = models.CharField(max_length=15, unique=True, validators=[
            RegexValidator(
                regex=r'^[6-9]\d{9}$',
                message="Please enter a valid 10-digit mobile number."
            )
        ],)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=10)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Supplier"              # singular name in sidebar and forms
        verbose_name_plural = "Suppliers"

    def __str__(self):
        return self.shop_name
