from django.db import models
from django.utils import timezone
from projects.models.Projects import Projects
from globals.models.Materials import Materials
from globals.models.Suppliers import Suppliers
from globals.models.Vehicles import Vehicles
from common.filters.adminModelFilter import validate_image_format

class ProjectMaterials(models.Model):

    
    # ---- PAYMENT STATUS ----
    PAYMENT_PENDING = 10
    PAYMENT_PARTIAL = 20
    PAYMENT_PAID = 30

    PAYMENT_STATUS_CHOICES = (
        (PAYMENT_PENDING, "Pending"),
        (PAYMENT_PARTIAL, "Partial"),
        (PAYMENT_PAID, "Paid"),
    )

    # ---- BASIC INFO ----
    project_id = models.ForeignKey( Projects, on_delete=models.CASCADE, related_name="project_material")

    material_id = models.ForeignKey( Materials, on_delete=models.CASCADE, related_name="material")

    # ---- QUANTITY ----
    quantity = models.DecimalField( max_digits=10, decimal_places=2, help_text="Quantity received")

    unit = models.CharField( max_length=20, help_text="Bags / Tons / CFT / Kg", null=True, blank=True)

    rate = models.DecimalField( max_digits=10, decimal_places=2, help_text="Rate per unit", null=True, blank=True)

    total_amount = models.DecimalField( max_digits=15, decimal_places=2)

    # ---- SUPPLIER DETAILS ----
    supplier_id = models.ForeignKey( Suppliers, on_delete=models.CASCADE, related_name="supplier")

    # ---- BILL & PAYMENT ----
    bill_no = models.CharField(max_length=100, null=True, blank=True)
    bill_date = models.DateField(blank=True, null=True)
    bill_image = models.FileField(
        upload_to='images/projects/Gallery/',
        validators=[validate_image_format],  
        blank=True,
        null=True
    )

    payment_status = models.SmallIntegerField(choices=PAYMENT_STATUS_CHOICES,default=PAYMENT_PENDING)

    paid_amount = models.DecimalField( max_digits=15, decimal_places=2, default=0, null=True, blank=True)
    balance = models.DecimalField( max_digits=15, decimal_places=2, default=0, null=True, blank=True)

    # ---- LOGISTICS ----
    vehicle_id = models.ForeignKey( Vehicles, on_delete=models.CASCADE, related_name="vehicle", blank=True, null=True)

    # ---- REMARKS ----
    remarks = models.TextField(null=True, blank=True)

    # ---- SYSTEM ----
    received_by = models.CharField( max_length=255, help_text="Site supervisor / store keeper", null=True, blank=True)

    received_date = models.DateField(default=timezone.now)

    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Project Material"
        verbose_name_plural = "Project Materials"
        ordering = ['-received_date']

    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.rate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.material_id.name} - {self.project_id.name}"
