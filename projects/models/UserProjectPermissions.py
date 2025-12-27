from django.db import models
from django.contrib.auth.models import User
from .Projects import Projects
from django.utils import timezone

class UserProjectPermissions(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assigned_projects"
    )   
    projects = models.ForeignKey(
        Projects,
        on_delete=models.CASCADE,
        related_name="assigned_users"
    )
    can_view = models.BooleanField(default=True)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        app_label = "auth"
        unique_together = ('user', 'projects')
        verbose_name = "User Project Permission"
        verbose_name_plural = "User Project Permissions"

    def __str__(self):
        return f"{self.user.username} → {self.projects.name}"