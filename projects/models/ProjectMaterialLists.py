from django.db import models
from django.utils import timezone
from projects.models.ProjectMaterials import ProjectMaterials
from globals.models.Materials import Materials
from globals.models.Suppliers import Suppliers
from globals.models.Vehicles import Vehicles
from common.filters.adminModelFilter import validate_image_format

class ProjectMaterialLists(models.Model):

    # ---- BASIC INFO ----
    project_material_id = models.ForeignKey( ProjectMaterials, on_delete=models.CASCADE, related_name="project_material_id")

    material_id = models.ForeignKey( Materials, on_delete=models.CASCADE, related_name="material")

    # ---- QUANTITY ----
    quantity = models.DecimalField( max_digits=10, decimal_places=2, help_text="Quantity received")

    unit = models.CharField( max_length=20, help_text="Bags / Tons / CFT / Kg", null=True, blank=True)

    rate = models.DecimalField( max_digits=10, decimal_places=2, help_text="Rate per unit", null=True, blank=True)

    amount = models.DecimalField( max_digits=15, decimal_places=2)

    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Project Material List"
        verbose_name_plural = "Project Material Lists"

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.rate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.material_id.name} - {self.project_material_id.project_id.name}"
