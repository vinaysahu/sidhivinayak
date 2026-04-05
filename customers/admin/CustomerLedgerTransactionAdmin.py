from django.contrib import admin

from ..models.Customers import Customers
from ..models.CustomerLedgerTransaction import CustomerLedgerTransaction
from ..forms.CustomerLedgerTransactionForm import CustomerLedgerTransactionForm
from common.filters.adminModelFilter import customDropdownFilterForAnotherTable
from django.db.models import Q
from django.contrib.auth.models import User
from projects.models.Projects import Projects
from django.db.models import F
from common.utils.format_currency import format_indian_currency
      
class CustomerLedgerTransactionAdmin(admin.ModelAdmin):

    form = CustomerLedgerTransactionForm

    list_display = ['paid_on', 'paid_to', 'payment_type','formatted_amount','detail' ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')

    list_filter = [customDropdownFilterForAnotherTable("Customers", "customers", "username", Customers, ["customer_ledger__customer_id"]  ), 'paid_to']

    
    def formatted_amount(self, obj):
        return format_indian_currency(obj.amount)
    formatted_amount.short_description = "Amount"

    def has_add_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    class Media:
            js = ('admin/js/amountFormat1.js',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.order_by(F('paid_on').asc(nulls_last=True))
        user = request.user

        if user.is_superuser:
            return qs

        return qs.filter(
            Q(user_ledger__creditor=user) | Q(user_ledger__debtor=user)
        ).distinct()
    


admin.site.register(CustomerLedgerTransaction,CustomerLedgerTransactionAdmin)
