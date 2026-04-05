from django.contrib import admin

from ..models.Customers import Customers
from ..models.CustomerLedgerTransaction import CustomerLedgerTransaction
from ..forms.CustomerLedgerTransactionForm import CustomerLedgerTransactionForm
from common.utils.format_currency import format_indian_currency
from django.db.models import Sum
from django.db.models.functions import Coalesce

class CustomerFilter(admin.SimpleListFilter):
    title = 'Customer'
    parameter_name = 'customer'

    def lookups(self, request, model_admin):
        customers = Customers.objects.all()
        return [
            (customer.id, f"{customer.first_name} {customer.last_name}")
            for customer in customers
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(customer_ledger__customer_id__id=self.value())
        return queryset
      
class CustomerLedgerTransactionAdmin(admin.ModelAdmin):

    form = CustomerLedgerTransactionForm

    list_display = ['paid_on', 'paid_to', 'payment_type','formatted_amount','detail' ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')

    # list_filter = [customDropdownFilterForAnotherTable("Customer Ledger", "Customer Ledger", "customer_id", CustomerLedger, ["customer_ledger__customer_id"]  ), 'paid_to']
    list_filter = [CustomerFilter, 'paid_to']

    search_fields = [
        'customer_ledger__customer_id__first_name',
        'customer_ledger__customer_id__last_name',
        'detail'
    ]

    def formatted_amount(self, obj):
        return format_indian_currency(obj.amount)
    formatted_amount.short_description = "Amount"

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            queryset = response.context_data['cl'].queryset

            total_amount = queryset.aggregate(
                total=Sum('amount')
            )['total']

            response.context_data['total_amount'] = format_indian_currency(total_amount)

        except (AttributeError, KeyError):
            pass

        return response

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

admin.site.register(CustomerLedgerTransaction,CustomerLedgerTransactionAdmin)
