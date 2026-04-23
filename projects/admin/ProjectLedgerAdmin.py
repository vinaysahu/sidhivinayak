from django.contrib import admin
from django.db.models import Sum
from ..models.ProjectLedger import ProjectLedger
from accounts.utils import format_indian_currency

@admin.register(ProjectLedger)
class ProjectLedgerAdmin(admin.ModelAdmin):
    list_display = ['project', 'entry_type', 'formatted_amount', 'entry_date', 'description', 'reference_type']
    list_filter = ['project', 'entry_type', 'entry_date']
    search_fields = ['project__name', 'description']
    list_select_related = True
    
    change_list_template = 'admin/projects/projectledger/change_list.html'
    
    # Make only auto-generated fields readonly
    readonly_fields = [
        'created_at'
    ]

    list_per_page = 15          # ← yeh add karo
    list_max_show_all = 100     # ← yeh add karo
    list_select_related = True

    def formatted_amount(self, obj):
        return format_indian_currency(obj.amount)
    formatted_amount.short_description = "Amount"

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def changelist_view(self, request, extra_context=None):
        # We need the filtered queryset to calculate the sum
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            # We look for 'cl' in the response context_data (it's the ChangeList instance)
            cl = response.context_data['cl']
            # Get the queryset from the ChangeList
            queryset = cl.get_queryset(request)
            # Calculate the sum
            total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0
            
            # Format the total amount
            total_amount_formatted = format_indian_currency(total_amount)
            
            # Add to context
            response.context_data['total_amount_formatted'] = total_amount_formatted
        except (AttributeError, KeyError):
            pass
            
        return response
