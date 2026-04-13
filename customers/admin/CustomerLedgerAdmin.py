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
from django.http import HttpResponseRedirect
from django.db import transaction

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
    

class CustomerLedgerRequestInline(admin.TabularInline):
    model = CustomerRequestTransaction
    extra = 0
    exclude = ('created_at', 'updated_at') 
    # max_num = 10 
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
        url = reverse('admin:accept_customer_request', args=[obj.id])
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

    inlines = [CustomerLedgerTransactionsInline,CustomerLedgerRequestInline]

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
        ]

        return custom_urls + urls

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
                    customer_request.status = CustomerRequestTransaction.STATUS_ACCEPTED   # accepted
                    customer_request.save()

            self.message_user(request, "Customer request accepted successfully.", level='success')
        except Exception as e:
            self.message_user(request, f"Error: {str(e)}", level='error')
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    def reject_customer_request(self, request, request_id):
        customer_request = CustomerRequestTransaction.objects.get(id=request_id)

        customer_request.status = CustomerRequestTransaction.STATUS_DELETED   # accepted
        customer_request.save()

        self.message_user(request, "Customer request rejected successfully.", level='success')

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

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
