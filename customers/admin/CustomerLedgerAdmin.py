from django.contrib import admin
from projects.models.Projects import Projects
from customers.models.CustomerLedger import CustomerLedger
from customers.models.CustomerLedgerTransaction import CustomerLedgerTransaction
from common.filters.adminModelFilter import TableForiegnKeyListFilter
from django.db.models import Q
from django.db.models import F
from num2words import num2words
from common.utils.format_currency import format_indian_currency
from django.utils.html import format_html

class CustomerLedgerTransactionsInline(admin.TabularInline):
    model = CustomerLedgerTransaction
    extra = 2
    exclude = ('created_at', 'updated_at') 
    # max_num = 10 
    verbose_name = "Customer Ledger Transaction"
    verbose_name_plural = "Customer Ledger Transactions"
    fields = ['paid_on','payment_type','amount','paid_to','detail'] 

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

      
class CustomerLedgerAdmin(admin.ModelAdmin):

    list_display = ['customer_id', 'project_id', 'project_house_id', 'formatted_amount', 'formatted_balance', 'paid_amount' ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')

    readonly_fields = ['paid_amount']

    def formatted_amount(self, obj):
        return format_indian_currency(obj.amount)
    formatted_amount.short_description = "Amount"

    # 👇 FORMAT BALANCE
    def formatted_balance(self, obj):
        return format_indian_currency(obj.balance)
    formatted_balance.short_description = "Balance"

    def paid_amount(self, obj):
        if obj.amount and obj.balance:
            paidAmount = obj.amount - obj.balance

            # number → words
            words = num2words(paidAmount, lang='en_IN').title()
            return format_html(
            "{}<br><small>({})</small>",
            format_indian_currency(paidAmount),
            words
        )
        return "-"
    paid_amount.short_description = "Paid Amount"

    inlines = [CustomerLedgerTransactionsInline]


    search_fields = ['amount', 'balance']
    list_filter = [ TableForiegnKeyListFilter("Projects", "project_id","name", Projects)]

    class Media:
            js = ('admin/js/amountFormat1.js',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user

        if user.is_superuser:
            return qs

        return qs.filter(
            Q(creditor=user) | Q(debtor=user)
        ).distinct()


admin.site.register(CustomerLedger,CustomerLedgerAdmin)
