from django.db import models
from django.utils import timezone
from .Categories import Categories
from common.filters.adminModelFilter import validate_image_size, validate_image_format

    
class CategoryMedia(models.Model):
    STATUS_TYPES = (
        (1, 'Image'),
        (2, 'Video'),
    )
    category_id = models.ForeignKey(Categories, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Category")
    type = models.SmallIntegerField(choices=STATUS_TYPES, default=1)
    file = models.ImageField(upload_to='images/categories/products/', validators=[validate_image_size, validate_image_format], default="images/default_logo.jpg", max_length=255)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Category Media"
        verbose_name_plural = "Category Media"

    def __str__(self):
        return f"Media for {self.category_id.name}"