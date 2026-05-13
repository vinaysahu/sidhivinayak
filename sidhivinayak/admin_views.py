from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
from sidhivinayak.admin_patches import _get_projects_data, _get_supplier_ledgers


@staff_member_required
def projects_overview(request):
    projects = _get_projects_data(limit=None)
    return render(request, 'admin/projects_overview.html', {
        'title': 'Under Construction — Projects Overview',
        'projects': projects,
    })


@staff_member_required
def suppliers_overview(request):
    from projects.models.Projects import Projects

    selected_project_id = request.GET.get('project_id', '')
    under_construction_projects = Projects.objects.filter(
        status=Projects.STATUS_ACTIVE
    ).order_by('name')

    project_id = int(selected_project_id) if selected_project_id.isdigit() else None
    supplier_ledgers = _get_supplier_ledgers(project_id=project_id, random_order=False)

    return render(request, 'admin/suppliers_overview.html', {
        'title': 'Suppliers with Pending Balance',
        'supplier_ledgers': supplier_ledgers,
        'projects': under_construction_projects,
        'selected_project_id': project_id,
    })


@staff_member_required
def customer_balance_chart_data(request):
    from customers.models.CustomerLedger import CustomerLedger

    project_id = request.GET.get('project_id', '')

    qs = (
        CustomerLedger.objects
        .filter(balance__gt=0)
        .select_related('customer_id', 'project_id', 'project_house_id')
        .order_by('-balance')
    )
    if project_id and project_id.isdigit():
        qs = qs.filter(project_id=project_id)

    labels, total_amounts, paid_amounts, balances = [], [], [], []

    for ledger in qs:
        customer = ledger.customer_id
        name = (
            f"{customer.first_name or ''} {customer.last_name or ''}".strip()
            or customer.username
        )
        house = f" (Plot {ledger.project_house_id.plot_no})" if ledger.project_house_id else ""
        labels.append(name + house)
        total_amounts.append(float(ledger.amount))
        paid_amounts.append(float(ledger.amount - ledger.balance))
        balances.append(float(ledger.balance))

    return JsonResponse({
        'labels': labels,
        'total_amounts': total_amounts,
        'paid_amounts': paid_amounts,
        'balances': balances,
    })
