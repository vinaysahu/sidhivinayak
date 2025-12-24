from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from .Projects import Projects
from workers.models.Workers import Workers

class ProjectWorkers(models.Model):

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

    project_id = models.ForeignKey(Projects, on_delete=models.CASCADE, verbose_name="Project")
    worker_id = models.ForeignKey(Workers, on_delete=models.CASCADE, verbose_name="Amenity")
    wages_type = models.SmallIntegerField(choices=WAGES_CHOICES, default=WAGES_PER_DAY)
    wages = models.IntegerField()
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Project Worker"              # singular name in sidebar and forms
        verbose_name_plural = "Project Workers"

    def __str__(self):
        return self.project_id.name

