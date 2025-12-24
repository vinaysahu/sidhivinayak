from django.db import models
from django.utils import timezone
from .Categories import Categories

class Feedbacks(models.Model):
    
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    category_id = models.ForeignKey("Categories", on_delete=models.SET_NULL, null=True, blank=True)  # Category model pe depend karta hai
    message = models.TextField()
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Feedback"              # singular name in sidebar and forms
        verbose_name_plural = "Feedbacks"

    def __str__(self):
        return self.name
