from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, Q
from ..models.CustomerLedgerTransaction import CustomerLedgerTransaction
from django.db import transaction
import logging

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

    ledger.balance = ledger.amount - credited + debited
    ledger.save(update_fields=['balance'])

@receiver(post_save, sender=CustomerLedgerTransaction)
def auto_create_user_ledger_transaction(sender, instance, created, **kwargs):
    """
    Auto-creates a UserLedgerTransaction when a CustomerLedgerTransaction is saved with payment_type 'credited',
    only if the paid_to user is a creditor in a UserLedger for the same project.
    """
    from accounts.models import UserLedger, UserLedgerTransaction

    logger = logging.getLogger(__name__)

    # STEP 1: Only proceed if payment_type is 'credited'
    if instance.payment_type != 'credited':
        return

    try:
        with transaction.atomic():
            customer_ledger = instance.customer_ledger
            paid_to = instance.paid_to
            project = customer_ledger.project_id

            # STEP 2: Only proceed if paid_to user is a creditor in a UserLedger for this project
            user_ledger = UserLedger.objects.filter(
                project_id=project,
                creditor=paid_to
            ).first()

            if not user_ledger:
                return

            # STEP 3: Prevent duplicate entries
            if UserLedgerTransaction.objects.filter(source_transaction=instance).exists():
                return

            # STEP 4: Create UserLedgerTransaction
            detail_prefix = f"Auto-entry from CustomerLedger #{customer_ledger.id} | "
            full_detail = detail_prefix + (instance.detail or "")

            UserLedgerTransaction.objects.create(
                user_ledger=user_ledger,
                amount=instance.amount,
                paid_on=instance.paid_on,
                payment_type=instance.payment_type,
                detail=full_detail,
                source_transaction=instance
            )
    except Exception as e:
        logger.error(f"Error in auto_create_user_ledger_transaction signal: {str(e)}")
