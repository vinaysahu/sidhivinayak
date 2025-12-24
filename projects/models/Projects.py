from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from globals.models.Countries import Countries
from globals.models.States import States
from globals.models.Cities import Cities
from globals.models.Localities import Localities

class Projects(models.Model):
    STATUS_ACTIVE = 10
    STATUS_INACTIVE = 20
    STATUS_DELETED = 30
    STATUS_UPCOMING = 40

    STATUS_CHOICES = (
        (STATUS_ACTIVE, "Under Constraction"),
        (STATUS_INACTIVE, "Completed"),
        (STATUS_DELETED, "Hold"),
        (STATUS_UPCOMING, "Up Coming"),
    )

    PROJECT_TYPES_HOUSE = 10
    PROJECT_TYPES_FLOOR = 20
    PROJECT_TYPES_MIXED = 30
    
    PROJECT_TYPES = (
        (PROJECT_TYPES_HOUSE, "House"),
        (PROJECT_TYPES_FLOOR, "Floor"),
        (PROJECT_TYPES_MIXED, "Mixed (House + Floors)"),
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    project_type = models.SmallIntegerField(choices=PROJECT_TYPES, default="mixed")

    country_id = models.ForeignKey(Countries, on_delete=models.CASCADE, related_name="country", blank=True, null=True, verbose_name="Country")
    state_id = models.ForeignKey(States, on_delete=models.CASCADE, related_name="state", blank=True, null=True, verbose_name="State")
    city_id = models.ForeignKey(Cities, on_delete=models.CASCADE, related_name="city", blank=True, null=True, verbose_name="City")
    locality_id = models.ForeignKey(Localities, on_delete=models.CASCADE, related_name="locality", blank=True, null=True, verbose_name="Locality")

    address = models.TextField(blank=True)
    landmark = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    area_sqyd = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    price_sqyd = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    dimensions = models.CharField(max_length=100, blank=True)
    facing = models.CharField(max_length=50, blank=True)

    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)
    seo_keywords = models.TextField(blank=True)

    main_image = models.ImageField(upload_to="images/projects/", blank=True, null=True)
    layout = models.ImageField(upload_to="images/projects/", blank=True, null=True)
    gallery_images = models.JSONField(blank=True, null=True)

    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Project"              # singular name in sidebar and forms
        verbose_name_plural = "Projects"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



