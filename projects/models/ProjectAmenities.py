from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from .Projects import Projects
from globals.models.Amenities import Amenities

class ProjectAmenities(models.Model):

    project_id = models.ForeignKey(Projects, on_delete=models.CASCADE, verbose_name="Project")
    amenity_id = models.ForeignKey(Amenities, on_delete=models.CASCADE, verbose_name="Amenity")
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Project Amenity"              # singular name in sidebar and forms
        verbose_name_plural = "Project Amenities"

    def __str__(self):
        return self.amenity_id.name



