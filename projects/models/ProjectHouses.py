from django.db import models
from .Projects import Projects
from customers.models.Customers import Customers
from django.utils import timezone

class ProjectHouses(models.Model):

    STATUS_AVAILABLE = 10
    STATUS_AGREMENT = 20
    STATUS_SOLD = 30
    STATUS_HOLD = 40

    STATUS_CHOICES = (
        (STATUS_AVAILABLE, "Available"),
        (STATUS_AGREMENT, "Agrement"),
        (STATUS_SOLD, "Sold"),
        (STATUS_HOLD, "Hold"),
    )

    project_id = models.ForeignKey(Projects, on_delete=models.CASCADE, related_name="project")
    customer_id = models.ForeignKey(Customers, on_delete=models.CASCADE, related_name="Customer", blank=True, null=True)
    # name = models.CharField(max_length=255)
    plot_no = models.IntegerField()
    area_sqyd = models.DecimalField(max_digits=10, decimal_places=2)
    builtup_area_sqft = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dimension = models.CharField(max_length=100, blank=True, null=True)

    bedrooms = models.IntegerField(default=2)
    bathrooms = models.IntegerField(default=2)
    Kitchen = models.IntegerField(default=1)
    balconies = models.IntegerField(default=0)
    parking = models.BooleanField(default=True)

    total_floors = models.SmallIntegerField(default=1)

    price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    house_images = models.JSONField(blank=True, null=True)
    layout = models.ImageField(upload_to="images/projects/house/", blank=True, null=True)
    complete_percentage = models.IntegerField(default=0)

    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=STATUS_AVAILABLE)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Project Houses"              # singular name in sidebar and forms
        verbose_name_plural = "Project Houses"

    def __str__(self):
        return f"House {self.plot_no} - {self.project_id.name}"
