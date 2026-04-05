from django.db import models
from .CustomerLedger import CustomerLedger   
from django.contrib.auth.models import User

class CustomerRequestTransaction(models.Model):

    PAYMENT_TYPE_CHOICES = (
        ('credited', 'Credited'),
        ('debited', 'Debited'),
    )

    STATUS_NEW = 10
    STATUS_ACCEPTED = 20
    STATUS_DELETED = 30

    STATUS_CHOICES = (
        (STATUS_NEW, "New"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_DELETED, "Deleted"),
    )

    customer_ledger = models.ForeignKey(
        CustomerLedger,
        on_delete=models.CASCADE,
        related_name='customer_transactions'
    )
    payment_type = models.CharField(
        max_length=10,
        choices=PAYMENT_TYPE_CHOICES,
        default='credited'
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    detail = models.TextField(blank=True, null=True)
    paid_on = models.DateField(blank=True, null=True)
    paid_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='paid_to_user'
    )
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer_ledger.customer_id.first_name} - {self.payment_type} - {self.amount}"
