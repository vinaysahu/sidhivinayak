from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from accounts.models.UserLedgerTransaction import UserLedgerTransaction

@receiver([post_save, post_delete], sender=UserLedgerTransaction)
def update_ledger_balance(sender, instance, **kwargs):
    ledger = instance.user_ledger

    credited = UserLedgerTransaction.objects.filter(
        user_ledger=ledger,
        payment_type='credited'
    ).aggregate(total=Sum('amount'))['total'] or 0

    debited = UserLedgerTransaction.objects.filter(
        user_ledger=ledger,
        payment_type='debited'
    ).aggregate(total=Sum('amount'))['total'] or 0

    ledger.balance = ledger.amount - credited + debited
    ledger.save()