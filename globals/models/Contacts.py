from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator

class Contacts(models.Model):
    STATUS_CHOICES = (
        (10, 'Active'),
        (20, 'Inactive'),
        (30, 'Deleted'),
    )
    PERONAL_CHOICES = (
        (1,"Yes"),
        (2, "No")
    )
    TYPE_CHOICES = (
        (1,"Shop"),
        (2, "Fair"),
        (3, "Other")
    )
    name = models.CharField(max_length=32, unique=True)
    mobile = models.CharField(max_length=15, unique=True, validators=[
            RegexValidator(
                regex=r'^[6-9]\d{9}$',
                message="Please enter a valid 10-digit mobile number."
            )
        ],)
    alt_mobile = models.CharField(max_length=15, validators=[
            RegexValidator(
                regex=r'^[6-9]\d{9}$',
                message="Please enter a valid 10-digit mobile number."
            )
        ], null=True, blank=True)
    reg_number = models.CharField(max_length=50, null=True, blank=True)
    personal = models.SmallIntegerField(choices=PERONAL_CHOICES, default=1)
    type = models.SmallIntegerField(choices=TYPE_CHOICES, default=1)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=10)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Contact"              # singular name in sidebar and forms
        verbose_name_plural = "Contacts"

    def __str__(self):
        return self.name
