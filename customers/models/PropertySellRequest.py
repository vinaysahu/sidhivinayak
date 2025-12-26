from django.db import models
from django.utils import timezone
from projects.models.Projects import Projects
from django.contrib.auth.models import User

class PropertySellRequest(models.Model):

    # ---- PROPERTY TYPE ----
    PROPERTY_FLAT = 10
    PROPERTY_HOUSE = 20
    PROPERTY_PLOT = 30

    PROPERTY_TYPE_CHOICES = (
        (PROPERTY_FLAT, "Flat"),
        (PROPERTY_HOUSE, "House"),
        (PROPERTY_PLOT, "Plot"),
    )

    # ---- STATUS ----
    STATUS_NEW = 10
    STATUS_CONTACTED = 20
    STATUS_SITE_VISIT = 30
    STATUS_DEAL_CLOSED = 40
    STATUS_REJECTED = 50

    STATUS_CHOICES = (
        (STATUS_NEW, "New Lead"),
        (STATUS_CONTACTED, "Contacted"),
        (STATUS_SITE_VISIT, "Site Visit"),
        (STATUS_DEAL_CLOSED, "Deal Closed"),
        (STATUS_REJECTED, "Rejected"),
    )

    # ---- OWNER DETAILS ----
    owner_name = models.CharField(max_length=255)
    phone_no = models.CharField(max_length=20)
    alt_phone_no = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # ---- PROPERTY DETAILS ----
    property_type = models.SmallIntegerField(
        choices=PROPERTY_TYPE_CHOICES
    )

    project = models.ForeignKey(
        Projects,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Agar property kisi known project me hai"
    )

    address = models.TextField(blank=True)
    area_sqyd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    dimension = models.CharField(max_length=100, blank=True, null=True)

    expected_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True
    )

    # ---- SELL REQUIREMENT ----
    reason_for_selling = models.CharField(
        max_length=255,
        blank=True,
        help_text="Urgent / Investment Exit / Other"
    )

    notes = models.TextField(
        blank=True,
        help_text="Broker notes / negotiation points"
    )

    # ---- SYSTEM ----
    status = models.SmallIntegerField(
        choices=STATUS_CHOICES,
        default=STATUS_NEW
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_property_sell_request'
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Property Sell Request"
        verbose_name_plural = "Property Sell Requests"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.owner_name} - {self.get_property_type_display()}"
