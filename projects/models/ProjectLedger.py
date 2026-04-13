from django.db import models
from .Projects import Projects
from .ProjectSupplierPayment import ProjectSupplierPayment
from .ProjectWorkerAttendances import ProjectWorkerAttendances

class ProjectLedger(models.Model):
    SUPPLIER_PAYMENT = 'SUPPLIER_PAYMENT'
    WORKER_PAYMENT = 'WORKER_PAYMENT'
    OTHER_EXPENSE = 'OTHER_EXPENSE'

    ENTRY_TYPE_CHOICES = (
        (SUPPLIER_PAYMENT, 'Supplier Payment'),
        (WORKER_PAYMENT, 'Worker Payment'),
        (OTHER_EXPENSE, 'Other Expense'),
    )

    project = models.ForeignKey(Projects, on_delete=models.CASCADE, related_name='ledger_entries')
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    entry_date = models.DateField()
    description = models.TextField()
    
    # Generic-like reference fields
    reference_type = models.CharField(max_length=50, null=True, blank=True, help_text="Model name e.g., supplier or worker")
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Direct links for convenience
    supplier_payment = models.ForeignKey(
        ProjectSupplierPayment, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='ledger_entries'
    )
    worker_attendance = models.ForeignKey(
        ProjectWorkerAttendances, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='ledger_entries'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Project Ledger"
        verbose_name_plural = "Project Ledgers"
        ordering = ['-entry_date', '-created_at']

    def __str__(self):
        return f"{self.get_entry_type_display()} - {self.amount} ({self.entry_date})"
