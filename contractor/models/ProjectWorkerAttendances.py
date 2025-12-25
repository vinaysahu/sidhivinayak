from django.db import models
from django.utils import timezone
from .ProjectWorkers import ProjectWorkers
from .Projects import Projects
from workers.models.Workers import Workers

class ProjectWorkerAttendances(models.Model):

    project_worker_id = models.ForeignKey(ProjectWorkers, on_delete=models.CASCADE, verbose_name="ProjectWorker", related_name="contractor_project_worker")
    project_id = models.ForeignKey(Projects, on_delete=models.CASCADE, verbose_name="Project",null=True, blank=True, related_name="contractor_project_id")
    worker_id = models.ForeignKey(Workers, on_delete=models.CASCADE, verbose_name="Worker",null=True, blank=True, related_name="contractor_project_worker_id")
    total_amount = models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)
    paid_amount = models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)
    remaining_amount = models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)
    working_date = models.DateField(default=timezone.now, null=True, blank=True)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Project Worker Attendance"              # singular name in sidebar and forms
        verbose_name_plural = "Project Worker Attendances"

    def __str__(self):
        return 'self.project_worker_id'
    
    def save(self, *args, **kwargs):
        self.project_id = self.project_worker_id.project_id
        self.worker_id = self.project_worker_id.worker_id
        super().save(*args, **kwargs)

