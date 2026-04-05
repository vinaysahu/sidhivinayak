from django.contrib import admin

from ..models.CustomerLedger import CustomerLedger
from ..models.CustomerRequestTransaction import CustomerRequestTransaction
from common.filters.adminModelFilter import customDropdownFilterForAnotherTable
from django.db.models import Q
from django.contrib.auth.models import User
from projects.models.Projects import Projects
from django.db.models import F
from common.utils.format_currency import format_indian_currency
      
class CustomerTransactionRequestAdmin(admin.ModelAdmin):

    list_display = ['paid_on', 'paid_to', 'payment_type','formatted_amount','detail', 'status' ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')
    
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

admin.site.register(CustomerRequestTransaction,CustomerTransactionRequestAdmin)
