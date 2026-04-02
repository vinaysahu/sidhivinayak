from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from ..models.CustomerLedgerTransaction import CustomerLedgerTransaction

@receiver([post_save, post_delete], sender=CustomerLedgerTransaction)
def update_ledger_balance(sender, instance, **kwargs):
    ledger = instance.customer_ledger

    credited = CustomerLedgerTransaction.objects.filter(
        customer_ledger=ledger,
        payment_type='credited'
    ).aggregate(total=Sum('amount'))['total'] or 0

    debited = CustomerLedgerTransaction.objects.filter(
        customer_ledger=ledger,
        payment_type='debited'
    ).aggregate(total=Sum('amount'))['total'] or 0

    ledger.balance = ledger.amount - credited 
    ledger.save()

    ledger.balance = ledger.balance + debited
    ledger.save()