from django.db import models
from django.utils import timezone
from projects.models.Projects import Projects

class CustomerEnquiry(models.Model):

    STATUS_NEW = 10
    STATUS_CONTACTED = 20
    STATUS_INTERESTED = 30
    STATUS_NOT_INTRESTED = 40
    STATUS_CONVERTED = 500

    STATUS_CHOICES = (
        (STATUS_NEW, "New"),
        (STATUS_CONTACTED, "Contacted"),
        (STATUS_INTERESTED, "Interested"),
        (STATUS_NOT_INTRESTED, "Not Interested"),
        (STATUS_CONVERTED, "Converted"),
    )

    project_id = models.ForeignKey(Projects, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Project")
    name = models.CharField(max_length=255)
    phone_no = models.CharField(max_length=20, unique=True)
    email = models.EmailField( max_length=255, null=True, blank=True, unique=True )
    requirement = models.TextField(help_text="Client requirement / expectation" )
    budget_min = models.DecimalField( max_digits=12, decimal_places=2, null=True, blank=True )
    budget_max = models.DecimalField( max_digits=12, decimal_places=2, null=True, blank=True )
    preferred_location = models.CharField( max_length=255, null=True, blank=True )
    property_type = models.CharField( max_length=100,
        choices=(
            ('residential', 'Residential'),
            ('commercial', 'Commercial'),
            ('plot', 'Plot'),
        ), default='residential'
    )
    notes = models.TextField( null=True, blank=True, help_text="Internal notes" )
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=10)
    follow_up_date = models.DateField( null=True, blank=True )
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Customer Enquiry"
        verbose_name_plural = "Customer Enquiries"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.phone_no})"
