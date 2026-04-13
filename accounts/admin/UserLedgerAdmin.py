from django.contrib import admin
from projects.models.Projects import Projects
from ..models.UserLedger import UserLedger
from ..models.UserLedgerTransaction import UserLedgerTransaction
from common.filters.adminModelFilter import TableForiegnKeyListFilter
from django.db.models import Q
from django.db.models import F
from num2words import num2words
from ..utils import format_indian_currency, amount_to_words
from django.utils.html import format_html

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
    list_display = ['creditor_name', 'debtor_name', 'project_id', 'formatted_amount', 'formatted_balance', 'paid_amount' ] 
    exclude = ('created_at', 'updated_at')
    readonly_fields = ['paid_amount']

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

    class Media:
        js = ('admin/js/amountFormat1.js',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_superuser:
            return qs
        return qs.filter(Q(creditor=user) | Q(debtor=user)).distinct()

admin.site.register(UserLedger, UserLedgerAdmin)
