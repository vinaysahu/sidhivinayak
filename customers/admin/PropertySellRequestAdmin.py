from django.contrib import admin
from ..models.PropertySellRequest import PropertySellRequest
      
class PropertySellRequestAdmin(admin.ModelAdmin):

    list_display_superuser = [ "owner_name", "phone_no", "alt_phone_no", "project", "email", "address", "area_sqyd", "dimension", "expected_price", "reason_for_selling", "notes", "status", "created_at", "updated_at" ] # grid mae kaisa view
    exclude_superuser = ('created_at', 'updated_at')       # Remove from FORM

    list_display_staff = [ "owner_name", "phone_no", "alt_phone_no", "email", "address", "area_sqyd", "dimension", "expected_price", "reason_for_selling", "notes", "status", "created_at", "updated_at" ]
    exclude_staff = ('created_by', 'created_at', 'updated_at', "project") 

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

        allowed_property_sell_request_ids = PropertySellRequest.objects.filter(
            created_by=request.user
        ).values_list('id', flat=True)

        return qs.filter(id__in=allowed_property_sell_request_ids)
    

admin.site.register(PropertySellRequest,PropertySellRequestAdmin)
