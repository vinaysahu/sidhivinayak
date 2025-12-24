from django.db import models
from django.contrib import admin
from django.utils import timezone
from django.utils.text import slugify

class Categories(models.Model):
    STATUS_CHOICES = (
        (10, 'Active'),
        (20, 'Inactive'),
        (30, 'Deleted'),
    )
    STATUS_CHOICES_ID={
        'active':10,
        'inactive':20,
        'deleted':30,
    }
    name = models.CharField(max_length=32)
    slug = models.SlugField(blank=True)
    parent_id = models.ForeignKey(
        'self',             # 👈 Self reference (same model)
        on_delete=models.SET_NULL,
        null=True,          # 👈 Top-level category ke liye parent null hoga
        blank=True,
        related_name='children',  # 👈 child categories ke reverse access ke liye
        verbose_name="Parent Category"
    )
    image = models.ImageField(upload_to='images/categories/', null=True, blank=True)
    icon = models.ImageField(upload_to='images/categories/icons', null=True, blank=True)
    short_description = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    seo_title = models.CharField(max_length=255, null=True, blank=True)
    seo_description = models.TextField(null=True, blank=True)
    seo_keywords = models.TextField(null=True, blank=True)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=10)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Category"              # singular name in sidebar and forms
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        slugVal = ''
        if self.parent_id:
            slugVal += self.parent_id.name+" "
            slugVal += self.name
        else :
            slugVal += self.name
        if not self.slug:
            self.slug = slugify(slugVal)
        super().save(*args, **kwargs)

    
    def __str__(self):
        return self.name
    
    @admin.display(
        description="Parent Category",
    )
    def get_parent_name(self):
        return self.parent_id.name if self.parent_id else "—"
    

