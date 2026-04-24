from django.contrib import admin
from django.utils.html import format_html
from ..models.ProjectSupplierLedger import ProjectSupplierLedger
from ..models.ProjectSupplierPayment import ProjectSupplierPayment
from accounts.utils import format_indian_currency, amount_to_words

class ProjectSupplierPaymentInline(admin.TabularInline):
    model = ProjectSupplierPayment
    extra = 1
    fields = ['payment_amount', 'payment_date', 'payment_mode', 'reference_number', 'notes']

@admin.register(ProjectSupplierLedger)
class ProjectSupplierLedgerAdmin(admin.ModelAdmin):
    list_display = [
        'project', 'supplier', 'item_description', 
        'item_date', 'formatted_total', 'formatted_paid', 
        'formatted_balance', 'balance_status'
    ]
    list_filter = ['project', 'supplier', 'item_date']
    search_fields = ['supplier__shop_name', 'item_description', 'project__name']
    readonly_fields = [
        'paid_amount', 'balance', 'created_at',
        'total_amount_display', 'paid_amount_display', 'balance_display'
    ]
    list_select_related = True
    save_on_top = True
    
    list_per_page = 15          # ← yeh add karo
    list_max_show_all = 100     # ← yeh add karo
    
    inlines = [ProjectSupplierPaymentInline]

    fieldsets = (
        (None, {
            'fields': ('project', 'supplier', 'item_description', 'item_date')
        }),
        ('Financials', {
            'fields': (
                'total_amount', 
                ('total_amount_display'),
                ('paid_amount_display'),
                ('balance_display'),
            )
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    # List view formatting
    def formatted_total(self, obj):
        return format_indian_currency(obj.total_amount)
    formatted_total.short_description = "Total"

    def formatted_paid(self, obj):
        return format_indian_currency(obj.paid_amount)
    formatted_paid.short_description = "Paid"

    def formatted_balance(self, obj):
        return format_indian_currency(obj.balance)
    formatted_balance.short_description = "Balance"

    def balance_status(self, obj):
        balance = obj.balance or 0
        if balance > 0:
            return format_html('<span style="color: red; font-weight: bold;">🔴 Baaki hai</span>')
        return format_html('<span style="color: green; font-weight: bold;">🟢 Paid</span>')
    balance_status.short_description = "Status"

    # Detail view (Change Form) display methods
    def total_amount_display(self, obj):
        amount = obj.total_amount or 0
        return format_html(
            '<div style="font-size: 1.2em; color: #2e7d32; font-weight: bold;">{}</div>'
            '<div style="color: #666;">{}</div>',
            format_indian_currency(amount),
            amount_to_words(amount)
        )
    total_amount_display.short_description = "Total Amount (Formatted)"

    def paid_amount_display(self, obj):
        amount = obj.paid_amount or 0
        return format_html(
            '<div style="font-size: 1.2em; color: #1976d2; font-weight: bold;">{}</div>'
            '<div style="color: #666;">{}</div>',
            format_indian_currency(amount),
            amount_to_words(amount)
        )
    paid_amount_display.short_description = "Paid Amount (Formatted)"

    def balance_display(self, obj):
        balance = obj.balance or 0
        color = "#d32f2f" if balance > 0 else "#2e7d32"
        return format_html(
            '<div style="font-size: 1.2em; color: {}; font-weight: bold;">{}</div>'
            '<div style="color: #666;">{}</div>',
            color,
            format_indian_currency(balance),
            amount_to_words(balance)
        )
    balance_display.short_description = "Balance (Formatted)"

    # Custom template for Top/Bottom summary
    change_form_template = 'admin/projects/projectsupplierledger/change_form.html'

    class Media:
        js = ('admin/js/amountFormat1.js',)
