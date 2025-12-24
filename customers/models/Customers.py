from django.db import models
from django.utils import timezone

class Customers(models.Model):

    STATUS_ACTIVE = 10
    STATUS_INACTIVE = 20
    STATUS_DELETED = 30

    STATUS_CHOICES = (
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
        (STATUS_DELETED, "Deleted"),
    )

    username = models.CharField(max_length=255,unique=True,db_index=True)

    auth_key = models.CharField(max_length=32)

    password_hash = models.CharField(max_length=255)

    password_reset_token = models.CharField(max_length=255,null=True,blank=True,db_index=True)

    email = models.EmailField(max_length=255,unique=True,db_index=True)

    first_name = models.CharField(max_length=255,null=True,blank=True)

    last_name = models.CharField(max_length=255,null=True,blank=True)

    phone_no = models.CharField(max_length=20,null=True,blank=True)

    alt_phone_no = models.CharField(max_length=20,null=True,blank=True)

    address = models.TextField(null=True,blank=True)

    dob = models.DateField(null=True,blank=True)

    avatar = models.ImageField(upload_to='images/customers/', null=True, blank=True)

    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=10)

    created_at = models.DateField(default=timezone.now)
    
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return self.username