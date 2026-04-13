from django.db import models
from django.utils import timezone
from .ProjectSupplierLedger import ProjectSupplierLedger

class ProjectSupplierPayment(models.Model):
    PAYMENT_MODE_CHOICES = (
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('online', 'Online'),
        ('bank_transfer', 'Bank Transfer'),
    )

    supplier_ledger = models.ForeignKey(
        ProjectSupplierLedger,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, default='cash')
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Project Supplier Payment"
        verbose_name_plural = "Project Supplier Payments"
        ordering = ['-payment_date', '-created_at']

    # save() and delete() override logic removed as it's now handled by signals
    # to maintain consistency and fulfill Task 3 requirements.

    def __str__(self):
        return f"Payment of {self.payment_amount} for {self.supplier_ledger.supplier.shop_name}"
