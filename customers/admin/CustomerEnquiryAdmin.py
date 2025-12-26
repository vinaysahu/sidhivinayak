from django.contrib import admin
from ..models.CustomerEnquiry import CustomerEnquiry
      
class CustomerEnquiryAdmin(admin.ModelAdmin):

    list_display_superuser = [ "name", "project_id", "phone_no", "email", "requirement", "budget_min", "notes", "follow_up_date", "notes", "status", "created_at", "updated_at" ]
    exclude_superuser = ('created_at', 'updated_at')

    list_display_staff = [ "name", "phone_no", "email", "requirement", "budget_min", "notes", "follow_up_date", "notes", "status", "created_at", "updated_at" ]
    exclude_staff = ('created_by', 'created_at', 'updated_at', 'project_id')

    def get_list_display(self, request):
        if request.user.is_superuser:
            return self.list_display_superuser
        return self.list_display_staff

    # 🔹 ROLE BASED EXCLUDE (FORM)
    def get_exclude(self, request, obj=None):
        if request.user.is_superuser:
            return self.exclude_superuser
        return self.exclude_staff

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        allowed_customer_enquiry_ids = CustomerEnquiry.objects.filter(
            created_by=request.user
        ).values_list('id', flat=True)

        return qs.filter(id__in=allowed_customer_enquiry_ids)
    

admin.site.register(CustomerEnquiry,CustomerEnquiryAdmin)
