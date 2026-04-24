from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum
from django.contrib.auth import get_user_model

from accounts.models.UserLedger import UserLedger
from accounts.models.UserLedgerTransaction import UserLedgerTransaction
from customers.models.CustomerLedgerTransaction import CustomerLedgerTransaction
from projects.models.Projects import Projects
from accounts.utils import format_indian_currency
from .forms import UserCustomerLedgerFilterForm

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
        paid_amount = (
            UserLedgerTransaction.objects
            .filter(user_ledger=ledger, payment_type='credited')
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
        .filter(paid_to=user_obj, customer_ledger__project_id=project_obj)
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

    return {
        'user_ledger_info': user_ledger_info,
        'customer_rows': customer_rows,
        'customer_grand_total': format_indian_currency(grand_total),
    }


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
