import json
from collections import defaultdict
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum
from django.contrib.auth import get_user_model

from accounts.models.UserLedger import UserLedger
from customers.models.CustomerLedger import CustomerLedger
from customers.models.CustomerLedgerTransaction import CustomerLedgerTransaction
from projects.models.Projects import Projects
from projects.models.ProjectLedger import ProjectLedger
from accounts.utils import format_indian_currency
from .forms import UserCustomerLedgerFilterForm, ProjectExpenseFilterForm, CustomerReportFilterForm

try:
    import weasyprint
except Exception:
    weasyprint = None

User = get_user_model()


def _build_report_data(user_obj, project_obj):
    # ── UserLedger info ──────────────────────────────────────────────────
    ledger = (
        UserLedger.objects
        .filter(creditor=user_obj, project_id=project_obj)
        .first()
    )

    user_ledger_info = None
    if ledger:
        # Calculate paid_amount directly from CustomerLedgerTransaction so it
        # stays in sync even if the auto-create signal was missed or amounts changed.
        paid_amount = (
            CustomerLedgerTransaction.objects
            .filter(
                paid_to=user_obj,
                customer_ledger__project_id=project_obj,
                payment_type='credited',
            )
            .aggregate(total=Sum('amount'))['total'] or 0
        )
        user_ledger_info = {
            'name': (
                f"{user_obj.first_name or ''} {user_obj.last_name or ''}".strip()
                or user_obj.username
            ),
            'project_name': project_obj.name,
            'amount': format_indian_currency(ledger.amount),
            'paid_amount': format_indian_currency(paid_amount),
            'balance': format_indian_currency(ledger.balance),
        }

    # ── Customer rows ────────────────────────────────────────────────────
    customer_qs = (
        CustomerLedgerTransaction.objects
        .filter(paid_to=user_obj, customer_ledger__project_id=project_obj,
                payment_type='credited')
        .values(
            'customer_ledger__customer_id',
            'customer_ledger__customer_id__first_name',
            'customer_ledger__customer_id__last_name',
            'customer_ledger__customer_id__username',
        )
        .annotate(total_paid=Sum('amount'))
        .order_by('customer_ledger__customer_id__first_name')
    )

    customer_rows = []
    grand_total = 0
    for row in customer_qs:
        first = row['customer_ledger__customer_id__first_name'] or ''
        last = row['customer_ledger__customer_id__last_name'] or ''
        username = row['customer_ledger__customer_id__username'] or ''
        name = f"{first} {last}".strip() or username
        grand_total += row['total_paid'] or 0
        customer_rows.append({
            'customer_name': name,
            'total_paid': format_indian_currency(row['total_paid']),
        })

    # ── Chart: ALL customers in this project from CustomerLedger ─────────
    cl_qs = (
        CustomerLedger.objects
        .filter(project_id=project_obj)
        .select_related('customer_id')
        .order_by('customer_id__first_name', 'customer_id__last_name')
    )
    chart_bar_labels  = []
    chart_bar_amounts = []   # total property amount
    chart_bar_paid    = []   # paid so far
    for cl in cl_qs:
        first = cl.customer_id.first_name or ''
        last  = cl.customer_id.last_name  or ''
        name  = f"{first} {last}".strip() or cl.customer_id.username
        total = float(cl.amount or 0)
        paid  = max(float((cl.amount or 0) - (cl.balance or 0)), 0)
        chart_bar_labels.append(name)
        chart_bar_amounts.append(total)
        chart_bar_paid.append(paid)

    # ── Per-customer transaction timeline ────────────────────────────────
    txn_qs = (
        CustomerLedgerTransaction.objects
        .filter(paid_to=user_obj, customer_ledger__project_id=project_obj,
                payment_type='credited')
        .order_by('paid_on')
        .values(
            'customer_ledger__customer_id__first_name',
            'customer_ledger__customer_id__last_name',
            'customer_ledger__customer_id__username',
            'paid_on',
            'amount',
        )
    )

    txn_by_customer = defaultdict(list)
    all_dates_set = set()
    for txn in txn_qs:
        first = txn['customer_ledger__customer_id__first_name'] or ''
        last  = txn['customer_ledger__customer_id__last_name']  or ''
        uname = txn['customer_ledger__customer_id__username']   or ''
        name  = f"{first} {last}".strip() or uname
        date_str = txn['paid_on'].isoformat() if txn['paid_on'] else ''
        if date_str:
            all_dates_set.add(date_str)
        txn_by_customer[name].append({
            'date':   date_str,
            'amount': float(txn['amount'] or 0),
        })

    # Sorted unique dates (X-axis for timeline chart)
    all_dates = sorted(all_dates_set)

    # Build one dataset per customer aligned to all_dates
    date_to_label = {d: _fmt_date(d) for d in all_dates}
    timeline_datasets = []
    for customer_name, txns in txn_by_customer.items():
        date_amount_map = defaultdict(float)
        for t in txns:
            if t['date']:
                date_amount_map[t['date']] += t['amount']
        timeline_datasets.append({
            'customer': customer_name,
            'data': [date_amount_map.get(d, 0) for d in all_dates],
        })

    return {
        'user_ledger_info':       user_ledger_info,
        'customer_rows':          customer_rows,
        'customer_grand_total':   format_indian_currency(grand_total),
        'chart_bar_labels':       json.dumps(chart_bar_labels),
        'chart_bar_amounts':      json.dumps(chart_bar_amounts),
        'chart_bar_paid':         json.dumps(chart_bar_paid),
        'chart_timeline_labels':  json.dumps([date_to_label[d] for d in all_dates]),
        'chart_timeline_datasets': json.dumps(timeline_datasets),
    }


def _fmt_date(iso: str) -> str:
    try:
        from datetime import date
        d = date.fromisoformat(iso)
        return d.strftime('%d %b %Y')
    except Exception:
        return iso


@staff_member_required
def user_customer_ledger_report(request):
    form = UserCustomerLedgerFilterForm(request.GET or None)
    context = {
        **admin.site.each_context(request),
        'form': form,
        'title': 'User Customer Ledger Report',
    }

    if request.GET.get('user') and request.GET.get('project'):
        if form.is_valid():
            user_obj = form.cleaned_data['user']
            project_obj = form.cleaned_data['project']
            report = _build_report_data(user_obj, project_obj)
            context.update({
                'report': report,
                'selected_user': user_obj,
                'selected_project': project_obj,
            })

    return render(request, 'reports/user_customer_ledger_report.html', context)


@staff_member_required
def get_projects_for_user(request):
    user_id = request.GET.get('user_id')
    if not user_id:
        return JsonResponse({'projects': []})
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return JsonResponse({'projects': []})

    project_ids = (
        CustomerLedgerTransaction.objects
        .filter(paid_to_id=user_id)
        .values_list('customer_ledger__project_id', flat=True)
        .distinct()
    )
    projects = Projects.objects.filter(id__in=project_ids).order_by('name').values('id', 'name')
    return JsonResponse({'projects': list(projects)})


@staff_member_required
def download_report_pdf(request):
    if weasyprint is None:
        return HttpResponse("PDF generation is unavailable on this server.", status=503)

    user_id = request.GET.get('user')
    project_id = request.GET.get('project')
    if not user_id or not project_id:
        return HttpResponse("User and Project are required.", status=400)

    try:
        user_obj = User.objects.get(pk=user_id)
        project_obj = Projects.objects.get(pk=project_id)
    except (User.DoesNotExist, Projects.DoesNotExist):
        return HttpResponse("Invalid user or project.", status=404)

    report = _build_report_data(user_obj, project_obj)
    from django.template.loader import render_to_string
    html_string = render_to_string('reports/user_customer_ledger_pdf.html', {
        'report': report,
        'selected_user': user_obj,
        'selected_project': project_obj,
    })

    try:
        pdf_bytes = weasyprint.HTML(
            string=html_string,
            base_url=request.build_absolute_uri('/')
        ).write_pdf()
    except OSError as e:
        return HttpResponse(f"PDF generation failed: {e}", status=500)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"ledger_{user_obj.username}_{project_obj.name}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ── Project Expenses Report ──────────────────────────────────────────────────

def _build_project_expense_data(project_obj):
    # ── ProjectLedger: breakdown by entry_type ───────────────────────────
    pl_totals = (
        ProjectLedger.objects
        .filter(project=project_obj)
        .values('entry_type')
        .annotate(total=Sum('amount'))
    )
    pl_map = {'SUPPLIER_PAYMENT': 0.0, 'WORKER_PAYMENT': 0.0, 'OTHER_EXPENSE': 0.0}
    for row in pl_totals:
        pl_map[row['entry_type']] = float(row['total'] or 0)
    pl_total = sum(pl_map.values())

    # ── UserLedger: all entries for this project ─────────────────────────
    ul_qs = (
        UserLedger.objects
        .filter(project_id=project_obj)
        .select_related('creditor', 'debtor')
        .order_by('creditor__first_name', 'creditor__last_name')
    )
    ul_rows = []
    ul_total = 0.0
    for ul in ul_qs:
        creditor = f"{ul.creditor.first_name} {ul.creditor.last_name}".strip() or ul.creditor.username
        debtor   = f"{ul.debtor.first_name} {ul.debtor.last_name}".strip()   or ul.debtor.username
        amt = float(ul.amount or 0)
        ul_total += amt
        ul_rows.append({
            'creditor':    creditor,
            'debtor':      debtor,
            'amount':      format_indian_currency(ul.amount),
            'amount_raw':  amt,
        })

    grand_total = pl_total + ul_total

    return {
        'pl_supplier':    format_indian_currency(pl_map['SUPPLIER_PAYMENT']),
        'pl_worker':      format_indian_currency(pl_map['WORKER_PAYMENT']),
        'pl_other':       format_indian_currency(pl_map['OTHER_EXPENSE']),
        'pl_total':       format_indian_currency(pl_total),
        'ul_rows':        ul_rows,
        'ul_total':       format_indian_currency(ul_total),
        'grand_total':    format_indian_currency(grand_total),
        # raw floats for chart
        'pl_supplier_raw': pl_map['SUPPLIER_PAYMENT'],
        'pl_worker_raw':   pl_map['WORKER_PAYMENT'],
        'pl_other_raw':    pl_map['OTHER_EXPENSE'],
        'ul_total_raw':    ul_total,
        'grand_total_raw': grand_total,
    }


@staff_member_required
def project_expenses_report(request):
    form = ProjectExpenseFilterForm(request.GET or None)
    context = {
        **admin.site.each_context(request),
        'form': form,
        'title': '',
    }
    if request.GET.get('project') and form.is_valid():
        project_obj = form.cleaned_data['project']
        context.update({
            'report': _build_project_expense_data(project_obj),
            'selected_project': project_obj,
        })
    return render(request, 'reports/project_expenses_report.html', context)


# ── Customer Report ──────────────────────────────────────────────────────────

def _build_customer_report_data(project_obj):
    from customers.models.CustomerLedger import CustomerLedger as CL
    ledgers = (
        CL.objects
        .filter(project_id=project_obj)
        .select_related('customer_id', 'project_house_id')
        .order_by('project_house_id__plot_no')
    )

    rows = []
    total_amount = 0
    total_paid = 0
    total_balance = 0

    chart_labels = []
    chart_amounts = []
    chart_paid = []
    chart_balance = []

    for cl in ledgers:
        house = cl.project_house_id
        customer = cl.customer_id
        amount = float(cl.amount or 0)
        balance = float(cl.balance or 0)
        paid = max(amount - balance, 0)

        customer_name = (
            f"{customer.first_name or ''} {customer.last_name or ''}".strip()
            or customer.username
        ) if customer else '—'

        plot_no = house.plot_no if house else '—'

        total_amount += amount
        total_paid += paid
        total_balance += balance

        rows.append({
            'plot_no': plot_no,
            'customer_name': customer_name,
            'amount': format_indian_currency(amount),
            'paid': format_indian_currency(paid),
            'balance': format_indian_currency(balance),
        })

        chart_labels.append(f"Plot #{plot_no} – {customer_name}")
        chart_amounts.append(amount)
        chart_paid.append(paid)
        chart_balance.append(balance)

    return {
        'rows': rows,
        'total_amount': format_indian_currency(total_amount),
        'total_paid': format_indian_currency(total_paid),
        'total_balance': format_indian_currency(total_balance),
        'chart_labels': json.dumps(chart_labels),
        'chart_amounts': json.dumps(chart_amounts),
        'chart_paid': json.dumps(chart_paid),
        'chart_balance': json.dumps(chart_balance),
    }


@staff_member_required
def customer_report(request):
    form = CustomerReportFilterForm(request.GET or None)
    context = {
        **admin.site.each_context(request),
        'form': form,
        'title': 'Customer Report',
    }
    if request.GET.get('project') and form.is_valid():
        project_obj = form.cleaned_data['project']
        context.update({
            'report': _build_customer_report_data(project_obj),
            'selected_project': project_obj,
        })
    return render(request, 'reports/customer_report.html', context)


@staff_member_required
def download_customer_report_pdf(request):
    if weasyprint is None:
        return HttpResponse("PDF generation is unavailable on this server.", status=503)

    project_id = request.GET.get('project')
    if not project_id:
        return HttpResponse("Project is required.", status=400)

    try:
        project_obj = Projects.objects.get(pk=project_id)
    except Projects.DoesNotExist:
        return HttpResponse("Invalid project.", status=404)

    report = _build_customer_report_data(project_obj)
    from django.template.loader import render_to_string
    html_string = render_to_string('reports/customer_report_pdf.html', {
        'report': report,
        'selected_project': project_obj,
    })

    try:
        pdf_bytes = weasyprint.HTML(
            string=html_string,
            base_url=request.build_absolute_uri('/')
        ).write_pdf()
    except OSError as e:
        return HttpResponse(f"PDF generation failed: {e}", status=500)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"customer_report_{project_obj.name}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
