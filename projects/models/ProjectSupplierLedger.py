from django.db import models
from django.utils import timezone
from .Projects import Projects
from globals.models.Suppliers import Suppliers

class ProjectSupplierLedger(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.CASCADE, related_name='supplier_ledgers')
    supplier = models.ForeignKey(Suppliers, on_delete=models.CASCADE, related_name='project_ledgers')
    item_description = models.TextField(help_text="Details of the items received")
    item_date = models.DateField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Project Supplier Ledger"
        verbose_name_plural = "Project Supplier Ledgers"
        ordering = ['-item_date', '-created_at']

    def save(self, *args, **kwargs):
        # Automatically calculate balance
        self.balance = self.total_amount - self.paid_amount
        super().save(*args, **kwargs)

    def update_totals(self):
        """
        Recalculates paid_amount and balance based on associated payments.
        """
        payments = self.payments.all()
        total_paid = sum(p.payment_amount for p in payments)
        self.paid_amount = total_paid
        self.balance = self.total_amount - self.paid_amount
        # Use update to avoid calling save() which might trigger recursion if not careful,
        # but here it's fine as we are calling it from payment's save.
        ProjectSupplierLedger.objects.filter(id=self.id).update(
            paid_amount=self.paid_amount,
            balance=self.balance
        )

    def __str__(self):
        return f"{self.supplier.shop_name} - {self.project.name} ({self.item_date})"
