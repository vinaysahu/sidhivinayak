from django.contrib import admin
from projects.models.Projects import Projects
from customers.models.CustomerLedger import CustomerLedger
from customers.models.CustomerLedgerTransaction import CustomerLedgerTransaction
from customers.models.CustomerRequestTransaction import CustomerRequestTransaction
from common.filters.adminModelFilter import TableForiegnKeyListFilter
from django.db.models import Q
from django.db.models import F
from num2words import num2words
from common.utils.format_currency import format_indian_currency
from django.utils.html import format_html
from django.urls import path, reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.db import transaction
from django.template.loader import render_to_string
try:
    import weasyprint
except Exception:
    weasyprint = None


class CustomerLedgerTransactionsInline(admin.TabularInline):
    model = CustomerLedgerTransaction
    extra = 2
    exclude = ('created_at', 'updated_at') 
    verbose_name = "Customer Ledger Transaction"
    verbose_name_plural = "Customer Ledger Transactions"
    fields = ['paid_on', 'payment_type', 'amount', 'paid_to', 'detail'] 

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by(F('paid_on').asc(nulls_last=True))

    def has_add_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CustomerLedgerRequestInline(admin.TabularInline):
    model = CustomerRequestTransaction
    extra = 0
    exclude = ('created_at', 'updated_at') 
    verbose_name = "Customer Transaction Request"
    verbose_name_plural = "Customer Transaction Requests" 
    fields = [
        'paid_on',
        'payment_type',
        'amount',
        'paid_to',
        'detail',
        'action_button'
    ]

    readonly_fields = [
        'paid_on',
        'payment_type',
        'amount',
        'paid_to',
        'detail',
        'action_button'
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status=10).order_by(F('paid_on').asc(nulls_last=True))
    
    def action_button(self, obj):
        url  = reverse('admin:accept_customer_request', args=[obj.id])
        url1 = reverse('admin:reject_customer_request', args=[obj.id])

        return format_html(
            '<a class="button" href="{}" '
            'style="background:#198754;color:white;padding:5px 10px;border-radius:4px;text-decoration:none;">'
            'Accept</a> '
            ' <a class="button" href="{}" '
            'style="background:red;color:white;padding:5px 10px;border-radius:4px;text-decoration:none;">'
            'Reject</a>',
            url, url1
        )

    action_button.short_description = 'Action'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CustomerLedgerAdmin(admin.ModelAdmin):

    list_select_related = True

    # ✅ 'ledger_actions' column add ki gayi
    list_display = [
        'customer_id',
        'project_id',
        'project_house_id',
        'formatted_amount',
        'formatted_balance',
        'paid_amount',
        'ledger_actions',        # ← naya column
    ]

    exclude = ('created_at', 'updated_at')
    readonly_fields = ['paid_amount']

    list_per_page = 15          # ← yeh add karo
    list_max_show_all = 100     # ← yeh add karo

    # ─── existing display methods ───────────────────────────────────────────

    def formatted_amount(self, obj):
        return format_indian_currency(obj.amount)
    formatted_amount.short_description = "Amount"

    def formatted_balance(self, obj):
        return format_indian_currency(obj.balance)
    formatted_balance.short_description = "Balance"

    def paid_amount(self, obj):
        if obj.amount and obj.balance:
            paidAmount = obj.amount - obj.balance
            words = num2words(paidAmount, lang='en_IN').title()
            return format_html(
                "{}<br><small>({})</small>",
                format_indian_currency(paidAmount),
                words
            )
        return "-"
    paid_amount.short_description = "Paid Amount"

    # ─── naya: Actions column with Download Ledger button ──────────────────

    def ledger_actions(self, obj):
        pdf_url = reverse('admin:download_customer_ledger', args=[obj.pk])
        return format_html(
            '<a href="{}" target="_blank" '
            'style="background:#0d6efd;color:white;padding:5px 12px;'
            'border-radius:4px;text-decoration:none;font-size:12px;'
            'white-space:nowrap;">📄 Download Ledger</a>',
            pdf_url
        )
    ledger_actions.short_description = "Actions"
    ledger_actions.allow_tags = True

    # ─── inlines ───────────────────────────────────────────────────────────

    inlines = [CustomerLedgerTransactionsInline, CustomerLedgerRequestInline]

    # ─── custom URLs ───────────────────────────────────────────────────────

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'accept-customer-request/<int:request_id>/',
                self.admin_site.admin_view(self.accept_customer_request),
                name='accept_customer_request'
            ),
            path(
                'reject-customer-request/<int:request_id>/',
                self.admin_site.admin_view(self.reject_customer_request),
                name='reject_customer_request'
            ),
            # ✅ naya URL — ledger PDF
            path(
                'customer-ledger/<int:ledger_id>/pdf/',
                self.admin_site.admin_view(self.download_ledger_pdf),
                name='download_customer_ledger'
            ),
        ]
        return custom_urls + urls

    # ─── existing request views ────────────────────────────────────────────

    def accept_customer_request(self, request, request_id):
        customer_request = CustomerRequestTransaction.objects.get(id=request_id)
        try:
            with transaction.atomic():
                customerLedgerEntry = CustomerLedgerTransaction.objects.create(
                    customer_ledger=customer_request.customer_ledger,
                    payment_type=customer_request.payment_type,
                    paid_on=customer_request.paid_on,
                    amount=customer_request.amount,
                    paid_to=customer_request.paid_to,
                    detail=customer_request.detail,
                )
                if customerLedgerEntry:
                    customer_request.status = CustomerRequestTransaction.STATUS_ACCEPTED
                    customer_request.save()

            self.message_user(request, "Customer request accepted successfully.", level='success')
        except Exception as e:
            self.message_user(request, f"Error: {str(e)}", level='error')

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    def reject_customer_request(self, request, request_id):
        customer_request = CustomerRequestTransaction.objects.get(id=request_id)
        customer_request.status = CustomerRequestTransaction.STATUS_DELETED
        customer_request.save()
        self.message_user(request, "Customer request rejected successfully.", level='success')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    # ─── naya: PDF generation view ─────────────────────────────────────────

    def download_ledger_pdf(self, request, ledger_id):
        ledger = CustomerLedger.objects.select_related().get(pk=ledger_id)

        # Saari transactions fetch karo date ke order mein
        transactions = CustomerLedgerTransaction.objects.filter(
            customer_ledger=ledger
        ).order_by(F('paid_on').asc(nulls_last=True))

        # Calculations
        paid_amount = (ledger.amount - ledger.balance) if (ledger.amount and ledger.balance) else 0
        paid_words  = num2words(int(paid_amount), lang='en_IN').title() if paid_amount else ""

        context = {
            'ledger':       ledger,
            'transactions': transactions,
            'paid_amount':  paid_amount,
            'paid_words':   paid_words,
            'formatted_amount':  format_indian_currency(ledger.amount),
            'formatted_balance': format_indian_currency(ledger.balance),
            'formatted_paid':    format_indian_currency(paid_amount),
        }

        if weasyprint is None:
            return HttpResponse("PDF generation is unavailable (weasyprint not installed).", status=503)
        html_string = render_to_string('admin/customers/customer_ledger_pdf.html', context)
        pdf_file    = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        # inline → browser mein khulega naye tab mein
        response['Content-Disposition'] = f'inline; filename="ledger_{ledger_id}.pdf"'
        return response

    # ─── filters / search ──────────────────────────────────────────────────

    search_fields = ['amount', 'balance']
    list_filter   = [TableForiegnKeyListFilter("Projects", "project_id", "name", Projects)]

    class Media:
        js = ('admin/js/amountFormat1.js',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()


admin.site.register(CustomerLedger, CustomerLedgerAdmin)