from django.contrib import admin
from django.shortcuts import redirect
from .models import UserCustomerLedger


@admin.register(UserCustomerLedger)
class UserCustomerLedgerAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        return redirect('/reports/user-customer-ledger/')
