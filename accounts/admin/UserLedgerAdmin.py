from django.contrib import admin
from projects.models.Projects import Projects
from ..models.UserLedger import UserLedger
from ..models.UserLedgerTransaction import UserLedgerTransaction
from common.filters.adminModelFilter import TableForiegnKeyListFilter
from django.db.models import Q
from django.db.models import F
from num2words import num2words
from django.urls import path, reverse
from ..utils import format_indian_currency, amount_to_words
from django.utils.html import format_html
from django.http import HttpResponseRedirect, HttpResponse
from django.template.loader import render_to_string
import weasyprint

class UserLedgerTransactionsInline(admin.TabularInline):
    model = UserLedgerTransaction
    extra = 1
    exclude = ('created_at', 'updated_at') 
    show_change_link = True
    verbose_name = "User Ledger Transaction"
    verbose_name_plural = "User Ledger Transactions"
    
    readonly_fields = [
        'amount_display', 'amount_words', 
        'paid_amount_display', 'paid_amount_words', 
        'balance_display', 'balance_words'
    ]
    
    fields = ['paid_on', 'payment_type', 'amount', 'amount_display', 'amount_words', 'detail'] 

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by(F('paid_on').asc(nulls_last=True))

    def amount_display(self, obj):
        if obj.id:
            return format_indian_currency(obj.amount)
        return "-"
    amount_display.short_description = "Amount (Fmt)"

    def amount_words(self, obj):
        if obj.id:
            return amount_to_words(obj.amount)
        return "-"
    amount_words.short_description = "Words"

    def paid_amount_display(self, obj):
        if obj.id and obj.user_ledger:
            paid_amt = obj.user_ledger.amount - obj.user_ledger.balance
            return format_indian_currency(paid_amt)
        return "-"
    paid_amount_display.short_description = "Paid (Fmt)"

    def paid_amount_words(self, obj):
        if obj.id and obj.user_ledger:
            paid_amt = obj.user_ledger.amount - obj.user_ledger.balance
            return amount_to_words(paid_amt)
        return "-"
    paid_amount_words.short_description = "Paid Words"

    def balance_display(self, obj):
        if obj.id and obj.user_ledger:
            return format_indian_currency(obj.user_ledger.balance)
        return "-"
    balance_display.short_description = "Bal (Fmt)"

    def balance_words(self, obj):
        if obj.id and obj.user_ledger:
            return amount_to_words(obj.user_ledger.balance)
        return "-"
    balance_words.short_description = "Bal Words"

    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

class UserLedgerAdmin(admin.ModelAdmin):
    list_select_related = True
    list_display = ['creditor_name', 'debtor_name', 'project_id', 'formatted_amount', 'formatted_balance', 'paid_amount', 'ledger_actions' ] 
    exclude = ('created_at', 'updated_at')
    readonly_fields = ['paid_amount']

    list_per_page = 15          # ← yeh add karo
    list_max_show_all = 100     # ← yeh add karo
    list_select_related = True

    def creditor_name(self, obj):
        if obj.creditor.first_name: 
            return obj.creditor.first_name + " " + obj.creditor.last_name
        return obj.creditor
    
    def debtor_name(self, obj):
        if obj.debtor.first_name: 
            return obj.debtor.first_name + " " + obj.debtor.last_name
        return obj.debtor

    def formatted_amount(self, obj):
        if obj.amount:
            words = amount_to_words(obj.amount)
            return format_html("{}<br><small>({})</small>", format_indian_currency(obj.amount), words)
        return "-"
    formatted_amount.short_description = "Amount"

    def formatted_balance(self, obj):
        if obj.balance:
            words = amount_to_words(obj.balance)
            return format_html("{}<br><small>({})</small>", format_indian_currency(obj.balance), words)
        return "-"
    formatted_balance.short_description = "Balance"

    def paid_amount(self, obj):
        if obj.amount and obj.balance:
            paidAmount = obj.amount - obj.balance
            words = amount_to_words(paidAmount)
            return format_html("{}<br><small>({})</small>", format_indian_currency(paidAmount), words)
        return "-"
    paid_amount.short_description = "Paid Amount"

    inlines = [UserLedgerTransactionsInline]
    search_fields = ['amount', 'balance']
    list_filter = [TableForiegnKeyListFilter("Projects", "project_id", "name", Projects)]

    # ─── naya: Actions column with Download Ledger button ──────────────────

    def ledger_actions(self, obj):
        pdf_url = reverse('admin:download_user_ledger', args=[obj.pk])
        return format_html(
            '<a href="{}" target="_blank" '
            'style="background:#0d6efd;color:white;padding:5px 12px;'
            'border-radius:4px;text-decoration:none;font-size:12px;'
            'white-space:nowrap;">📄 Download Ledger</a>',
            pdf_url
        )
    ledger_actions.short_description = "Actions"
    ledger_actions.allow_tags = True
    

    class Media:
        js = ('admin/js/amountFormat1.js',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_superuser:
            return qs
        return qs.filter(Q(creditor=user) | Q(debtor=user)).distinct()
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # ✅ naya URL — ledger PDF
            path(
                'user-ledger/<int:ledger_id>/pdf/',
                self.admin_site.admin_view(self.download_ledger_pdf),
                name='download_user_ledger'
            ),
        ]
        return custom_urls + urls
    
    def download_ledger_pdf(self, request, ledger_id):
        ledger = UserLedger.objects.select_related().get(pk=ledger_id)

        # Saari transactions fetch karo date ke order mein
        transactions = UserLedgerTransaction.objects.filter(
            user_ledger=ledger
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

        html_string = render_to_string('admin/accounts/user_ledger_pdf.html', context)
        pdf_file    = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        # inline → browser mein khulega naye tab mein
        response['Content-Disposition'] = f'inline; filename="ledger_{ledger_id}.pdf"'
        return response


admin.site.register(UserLedger, UserLedgerAdmin)
