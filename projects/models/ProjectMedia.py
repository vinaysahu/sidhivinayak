from django.db import models
from django.utils import timezone
from .Projects import Projects
from common.filters.adminModelFilter import validate_file_extension
import os
    
class ProjectMedia(models.Model):
    FILE_TYPES = (
        (1, 'Image'),
        (2, 'Video'),
        (3, 'PDF'),
    )
    project_id = models.ForeignKey(Projects, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Project")
    name = models.CharField(max_length=255, null=True, blank=True)
    type = models.SmallIntegerField(choices=FILE_TYPES, default=1)
    file = models.FileField(
        upload_to='images/projects/Gallery/',
        validators=[validate_file_extension],  
        blank=False,
        null=False
    )
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Project Media"
        verbose_name_plural = "Project Media"

    @property
    def file_extension(self):
        return self.file.name.split('.')[-1].lower()

    def __str__(self):
        return f"Media for {self.project_id.name}"
    
    def save(self, *args, **kwargs):
        ext = os.path.splitext(self.file.name)[1].lower()

        if ext in ['.jpg', '.jpeg', '.png', '.gif']:
            self.type = 1
        elif ext in ['.mp4', '.mov', '.avi', '.mkv']:
            self.type = 2
        elif ext == '.pdf':
            self.type = 3

        super().save(*args, **kwargs)