from django.contrib.admin import AdminSite
from django.db.models import Count, Sum, Q

_original_index = AdminSite.index


def _get_projects_data(limit=None):
    from projects.models.Projects import Projects
    from projects.models.ProjectHouses import ProjectHouses
    from common.utils.format_currency import format_indian_currency

    qs = (
        Projects.objects
        .filter(status=Projects.STATUS_ACTIVE)
        .annotate(
            total_houses=Count('project', distinct=True),
            available_houses=Count('project', filter=Q(project__status=ProjectHouses.STATUS_AVAILABLE), distinct=True),
            agreement_houses=Count('project', filter=Q(project__status=ProjectHouses.STATUS_AGREMENT), distinct=True),
            hold_houses=Count('project', filter=Q(project__status=ProjectHouses.STATUS_HOLD), distinct=True),
            sold_houses=Count('project', filter=Q(project__status=ProjectHouses.STATUS_SOLD), distinct=True),
            total_expenses=Sum('ledger_entries__amount'),
        )
        .order_by('-created_at')
    )
    if limit:
        qs = qs[:limit]

    result = []
    for p in qs:
        result.append({
            'id': p.id,
            'name': p.name,
            'total_houses': p.total_houses or 0,
            'available_houses': p.available_houses or 0,
            'agreement_houses': p.agreement_houses or 0,
            'hold_houses': p.hold_houses or 0,
            'sold_houses': p.sold_houses or 0,
            'total_expenses': format_indian_currency(p.total_expenses),
        })
    return result


def _get_supplier_ledgers(project_id=None, limit=None, random_order=False):
    from projects.models.ProjectSupplierLedger import ProjectSupplierLedger
    from common.utils.format_currency import format_indian_currency

    qs = (
        ProjectSupplierLedger.objects
        .filter(balance__gt=0)
        .select_related('supplier', 'project')
    )
    if project_id:
        qs = qs.filter(project_id=project_id)

    if random_order:
        qs = qs.order_by('?')
    else:
        qs = qs.order_by('-balance')

    if limit:
        qs = qs[:limit]

    result = []
    for entry in qs:
        result.append({
            'id': entry.id,
            'supplier_name': entry.supplier.shop_name,
            'project_name': entry.project.name,
            'item_description': entry.item_description,
            'item_date': entry.item_date,
            'total_amount': format_indian_currency(entry.total_amount),
            'paid_amount': format_indian_currency(entry.paid_amount),
            'balance': format_indian_currency(entry.balance),
        })
    return result


def _dashboard_index(self, request, extra_context=None):
    from projects.models.Projects import Projects
    from customers.models.CustomerLedger import CustomerLedger
    from projects.models.ProjectSupplierLedger import ProjectSupplierLedger

    extra_context = extra_context or {}
    extra_context['dashboard_stats'] = {
        'under_construction': Projects.objects.filter(status=Projects.STATUS_ACTIVE).count(),
        'completed': Projects.objects.filter(status=Projects.STATUS_INACTIVE).count(),
        'customers_with_balance': (
            CustomerLedger.objects
            .filter(balance__gt=0)
            .values('customer_id')
            .distinct()
            .count()
        ),
        'suppliers_with_balance': (
            ProjectSupplierLedger.objects
            .filter(balance__gt=0)
            .values('supplier')
            .distinct()
            .count()
        ),
    }
    extra_context['latest_projects'] = _get_projects_data(limit=5)
    extra_context['top_supplier_ledgers'] = _get_supplier_ledgers(limit=5, random_order=True)
    extra_context['under_construction_projects'] = (
        Projects.objects.filter(status=Projects.STATUS_ACTIVE).order_by('name')
    )
    return _original_index(self, request, extra_context)


AdminSite.index = _dashboard_index
