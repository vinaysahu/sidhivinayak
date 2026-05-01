from django.db import models
from .ChatSession import ChatSession


class PendingTransaction(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    KIND_CUSTOMER_TXN = "customer_txn"
    KIND_SUPPLIER_PAYMENT = "supplier_payment"
    KIND_WORKER_ATTENDANCE = "worker_attendance"
    KIND_CHOICES = (
        (KIND_CUSTOMER_TXN, "Customer Ledger Transaction"),
        (KIND_SUPPLIER_PAYMENT, "Supplier Payment"),
        (KIND_WORKER_ATTENDANCE, "Worker Attendance"),
    )

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="pending_transactions",
    )
    kind = models.CharField(
        max_length=32,
        choices=KIND_CHOICES,
        default=KIND_CUSTOMER_TXN,
    )
    payload = models.JSONField(
        help_text=(
            "Proposed payload. Shape depends on `kind` - see propose_* "
            "tool implementations in chat/services/tools.py."
        )
    )
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    created_transaction = models.ForeignKey(
        "customers.CustomerLedgerTransaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_pending_transactions",
    )
    created_supplier_payment = models.ForeignKey(
        "projects.ProjectSupplierPayment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_pending_transactions",
    )
    created_worker_attendance = models.ForeignKey(
        "projects.ProjectWorkerAttendances",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_pending_transactions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Pending AI Transaction"
        verbose_name_plural = "Pending AI Transactions"

    def __str__(self):
        return f"Pending #{self.id} ({self.kind}/{self.status}) - session #{self.session_id}"
