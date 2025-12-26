from django.db import models
from .WorkerTypes import WorkerTypes
from django.contrib.auth.models import User
from common.middleware.threadlocal import get_current_user
from django.utils import timezone
from django.core.validators import RegexValidator

class Workers(models.Model):
    STATUS_ACTIVE = 10
    STATUS_INACTIVE = 20
    STATUS_DELETED = 30

    STATUS_CHOICES = (
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
        (STATUS_DELETED, "Deleted"),
    )

    WAGES_PER_DAY = 10
    WAGES_PER_HOUR = 20
    WAGES_PER_SQ_FT = 30
    WAGES_LUM_SUM = 40

    WAGES_CHOICES = (
        (WAGES_PER_DAY, "Per Day"),
        (WAGES_PER_HOUR, "Per Hour"),
        (WAGES_PER_SQ_FT, "Per SQ FT"),
        (WAGES_LUM_SUM, "Lum Sum"),
    )

    name = models.CharField(max_length=255)
    worker_type_id = models.ForeignKey(
        WorkerTypes, 
        on_delete=models.CASCADE, 
        verbose_name='worker'
    )
    wages = models.IntegerField()
    ratting = models.IntegerField(null=True, blank=True)
    mobile = models.CharField(max_length=15, unique=True, validators=[
            RegexValidator(
                regex=r'^[6-9]\d{9}$',
                message="Please enter a valid 10-digit mobile number."
            )
        ],)
    
    wages_type = models.SmallIntegerField(choices=WAGES_CHOICES, default=WAGES_PER_DAY)
    
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_projects'
    )
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Worker"              # singular name in sidebar and forms
        verbose_name_plural = "Workers"

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.pk:  # CREATE time
            if not self.created_by:
                user = get_current_user()
                if user and user.is_authenticated and not user.is_superuser:
                    self.created_by = user
        super().save(*args, **kwargs)
