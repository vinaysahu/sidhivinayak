from django.contrib import admin
from ..models.UserLedger import UserLedger
from ..models.UserLedgerTransaction import UserLedgerTransaction
from ..forms.UserLedgerTransactionForm import UserLedgerTransactionForm
from common.filters.adminModelFilter import customDropdownFilterForAnotherTable
from django.db.models import Q
from django.contrib.auth.models import User
from projects.models.Projects import Projects
from django.db.models import F
from ..utils import format_indian_currency, amount_to_words
from django.utils.html import format_html

class UserLedgerTransactionAdmin(admin.ModelAdmin):
    form = UserLedgerTransactionForm
    list_display = ['paid_on', 'payment_type', 'formatted_amount', 'detail']
    exclude = ('created_at', 'updated_at')
    
    readonly_fields = [
        'amount_display', 'amount_words', 
        'paid_amount_display', 'paid_amount_words', 
        'balance_display', 'balance_words'
    ]

    fieldsets = (
        (None, {
            'fields': (
                'user_ledger', 'payment_type', 'paid_on', 'amount', 'detail'
            )
        }),
        ('Summary (Currency Display)', {
            'fields': (
                ('amount_display', 'amount_words'),
                ('paid_amount_display', 'paid_amount_words'),
                ('balance_display', 'balance_words'),
            ),
            'classes': ('collapse', 'summary-box'), # Optional styling
        }),
    )

    list_per_page = 15          # ← yeh add karo
    list_max_show_all = 100     # ← yeh add karo
    list_select_related = True

    def formatted_amount(self, obj):
        return format_indian_currency(obj.amount)
    formatted_amount.short_description = "Amount"

    # Readonly field implementations
    def amount_display(self, obj):
        return format_indian_currency(obj.amount)
    amount_display.short_description = "Amount (Formatted)"

    def amount_words(self, obj):
        return amount_to_words(obj.amount)
    amount_words.short_description = "Amount in Words"

    def paid_amount_display(self, obj):
        if obj.user_ledger:
            paid_amt = obj.user_ledger.amount - obj.user_ledger.balance
            return format_indian_currency(paid_amt)
        return "-"
    paid_amount_display.short_description = "Paid Amount (Formatted)"

    def paid_amount_words(self, obj):
        if obj.user_ledger:
            paid_amt = obj.user_ledger.amount - obj.user_ledger.balance
            return amount_to_words(paid_amt)
        return "-"
    paid_amount_words.short_description = "Paid Amount in Words"

    def balance_display(self, obj):
        if obj.user_ledger:
            return format_indian_currency(obj.user_ledger.balance)
        return "-"
    balance_display.short_description = "Balance (Formatted)"

    def balance_words(self, obj):
        if obj.user_ledger:
            return amount_to_words(obj.user_ledger.balance)
        return "-"
    balance_words.short_description = "Balance in Words"

    def get_list_filter(self, request):
        if request.user.is_superuser:
            return [
                customDropdownFilterForAnotherTable(
                    "User", "user", "first_name", User,
                    filter_fields=["user_ledger__creditor_id", "user_ledger__debtor_id"]
                ),
                customDropdownFilterForAnotherTable(
                    "Project", "project", "name", Projects,
                    filter_fields=["user_ledger__project_id"]
                )
            ]
        return []

    class Media:
        js = ('admin/js/amountFormat1.js',)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user_ledger')
        qs = qs.order_by(F('paid_on').asc(nulls_last=True))
        user = request.user
        if user.is_superuser:
            return qs
        return qs.filter(
            Q(user_ledger__creditor=user) | Q(user_ledger__debtor=user)
        ).distinct()

admin.site.register(UserLedgerTransaction, UserLedgerTransactionAdmin)
