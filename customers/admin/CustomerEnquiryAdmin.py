from django.contrib import admin
from ..models.CustomerEnquiry import CustomerEnquiry
from django.utils.html import format_html
from django.contrib.auth.hashers import make_password
import secrets
      
class CustomerEnquiryAdmin(admin.ModelAdmin):

    list_display = [ "name", "project_id", "phone_no", "email", "requirement", "budget_min", "notes", "follow_up_date", "notes", "status", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        allowed_customer_enquiry_ids = CustomerEnquiry.objects.filter(
            created_by=request.user
        ).values_list('id', flat=True)

        return qs.filter(id__in=allowed_customer_enquiry_ids)
    

admin.site.register(CustomerEnquiry,CustomerEnquiryAdmin)
