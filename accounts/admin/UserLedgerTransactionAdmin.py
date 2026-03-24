from django.contrib import admin

from ..models.UserLedger import UserLedger
from ..models.UserLedgerTransaction import UserLedgerTransaction
from ..forms.UserLedgerTransactionForm import UserLedgerTransactionForm
from common.filters.adminModelFilter import customDropdownFilterForAnotherTable
from django.db.models import Q
from django.contrib.auth.models import User
from projects.models.Projects import Projects
from django.db.models import F
from common.utils.format_currency import format_indian_currency
      
class UserLedgerTransactionAdmin(admin.ModelAdmin):

    form = UserLedgerTransactionForm

    list_display = ['paid_on','payment_type','formatted_amount','detail' ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')

    list_filter = [customDropdownFilterForAnotherTable("User", "user", "first_name", User,  filter_fields=["user_ledger__creditor_id","user_ledger__debtor_id"]  )]

    def get_list_filter(self, request):
        if request.user.is_superuser:
            return [
                customDropdownFilterForAnotherTable(
                    "User",
                    "user",
                    "first_name",
                    User,
                    filter_fields=[
                        "user_ledger__creditor_id",
                        "user_ledger__debtor_id"
                    ]
                ),
                customDropdownFilterForAnotherTable(
                    "Project",
                    "project",
                    "name",
                    Projects,
                    filter_fields=[
                        "user_ledger__project_id",
                    ]
                )
            ]
        return []
    
    def formatted_amount(self, obj):
        return format_indian_currency(obj.amount)
        return f"₹ {obj.amount:,.2f}"
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
    


admin.site.register(UserLedgerTransaction,UserLedgerTransactionAdmin)
