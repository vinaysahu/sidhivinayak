from django.db import models
from .UserLedger import UserLedger   # assume same app
from decimal import Decimal, InvalidOperation
import re
class UserLedgerTransaction(models.Model):

    PAYMENT_TYPE_CHOICES = (
        ('credited', 'Credited'),
        ('debited', 'Debited'),
    )

    user_ledger = models.ForeignKey(
        UserLedger,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    payment_type = models.CharField(
        max_length=10,
        choices=PAYMENT_TYPE_CHOICES
    )
    paid_on = models.DateField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    detail = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_ledger.creditor.first_name} - {self.payment_type} - {self.amount}"
