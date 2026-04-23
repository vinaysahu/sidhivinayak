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
    Auto-creates a UserLedgerTransaction when a CustomerLedgerTransaction is saved with payment_type 'credited'.
    """
    from accounts.models import UserLedger, UserLedgerTransaction

    logger = logging.getLogger(__name__)

    # STEP 1: Check payment_type
    # Only proceed if payment_type is 'credited'
    if instance.payment_type != 'credited':
        return

    try:
        with transaction.atomic():
            # STEP 2: Check paid_to user against CustomerLedger parties or superuser
            customer_ledger = instance.customer_ledger
            paid_to = instance.paid_to

            is_valid_party = False
            if paid_to.is_superuser:
                is_valid_party = True
            else:
                # Check if creditor/debtor fields exist on CustomerLedger (fallback to project if not)
                creditor = getattr(customer_ledger, 'creditor', None)
                debtor = getattr(customer_ledger, 'debtor', None)

                if creditor == paid_to or debtor == paid_to:
                    is_valid_party = True
                else:
                    # If fields are missing on CustomerLedger, check if user is party in any UserLedger for this project
                    project = customer_ledger.project_id
                    if UserLedger.objects.filter(project_id=project).filter(Q(creditor=paid_to) | Q(debtor=paid_to)).exists():
                        is_valid_party = True

            if not is_valid_party:
                return

            # STEP 3: Prevent duplicate entries
            # Check if UserLedgerTransaction already exists referencing this CustomerLedgerTransaction
            if UserLedgerTransaction.objects.filter(source_transaction=instance).exists():
                return

            # STEP 4: Create UserLedgerTransaction
            # Find the UserLedger belonging to paid_to user for this project
            project = customer_ledger.project_id
            user_ledger = UserLedger.objects.filter(
                project_id=project
            ).filter(
                Q(creditor=paid_to) | Q(debtor=paid_to)
            ).first()

            if not user_ledger:
                # If no matching UserLedger found, we cannot create the transaction
                return

            detail_prefix = f"Auto-entry from CustomerLedger #{customer_ledger.id} | "
            full_detail = detail_prefix + (instance.detail or "")

            UserLedgerTransaction.objects.create(
                user_ledger=user_ledger,
                amount=instance.amount,
                paid_on=instance.paid_on,
                payment_type=instance.payment_type, # 'credited'
                detail=full_detail,
                source_transaction=instance
            )
    except Exception as e:
        logger.error(f"Error in auto_create_user_ledger_transaction signal: {str(e)}")
