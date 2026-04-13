from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from ..models.ProjectSupplierPayment import ProjectSupplierPayment
from ..models.ProjectWorkerAttendances import ProjectWorkerAttendances
from ..models.ProjectLedger import ProjectLedger
from ..models.ProjectSupplierLedger import ProjectSupplierLedger

# Signal 1 — SupplierPaymentSignal
@receiver(post_save, sender=ProjectSupplierPayment)
def supplier_payment_saved(sender, instance, created, **kwargs):
    # a) Recalculate ProjectSupplierLedger (already has update_totals method)
    instance.supplier_ledger.update_totals()

    # b) ProjectLedger automatic entry
    description = f"Supplier {instance.supplier_ledger.supplier.shop_name} ko payment - {instance.supplier_ledger.item_description}"
    
    ProjectLedger.objects.update_or_create(
        supplier_payment=instance,
        defaults={
            'project': instance.supplier_ledger.project,
            'entry_type': ProjectLedger.SUPPLIER_PAYMENT,
            'amount': instance.payment_amount,
            'entry_date': instance.payment_date,
            'description': description,
            'reference_type': 'supplier',
            'reference_id': instance.supplier_ledger.supplier.id,
        }
    )

@receiver(post_delete, sender=ProjectSupplierPayment)
def supplier_payment_deleted(sender, instance, **kwargs):
    # Recalculate ProjectSupplierLedger
    # Use a try-except because the ledger might be deleted too (cascade)
    try:
        instance.supplier_ledger.update_totals()
    except ProjectSupplierLedger.DoesNotExist:
        pass
    
    # ProjectLedger entry is automatically deleted via ForeignKey cascade

# Signal 2 — ProjectWorkerAttendanceSignal
@receiver(post_save, sender=ProjectWorkerAttendances)
def worker_attendance_saved(sender, instance, created, **kwargs):
    # Only create/update ledger if there's a payment amount (wage) and necessary foreign keys exist
    if instance.paid_amount and instance.paid_amount > 0 and instance.project_id and instance.worker_id:
        worker_name = instance.worker_id.name
        
        description = f"Worker {worker_name} - {instance.working_date} ki attendance payment"
        
        ProjectLedger.objects.update_or_create(
            worker_attendance=instance,
            defaults={
                'project': instance.project_id,
                'entry_type': ProjectLedger.WORKER_PAYMENT,
                'amount': instance.paid_amount,
                'entry_date': instance.working_date or instance.created_at,
                'description': description,
                'reference_type': 'worker',
                'reference_id': instance.worker_id.id,
            }
        )
    else:
        # If amount became 0/None or foreign keys are missing, remove from ledger if it existed
        ProjectLedger.objects.filter(worker_attendance=instance).delete()

@receiver(post_delete, sender=ProjectWorkerAttendances)
def worker_attendance_deleted(sender, instance, **kwargs):
    # ProjectLedger entry is automatically deleted via ForeignKey cascade
    pass
