from django.contrib import admin
from ..models.PropertySellRequest import PropertySellRequest
      
class PropertySellRequestAdmin(admin.ModelAdmin):

    list_display = [ "owner_name", "phone_no", "alt_phone_no", "email", "address", "area_sqyd", "dimension", "expected_price", "reason_for_selling", "notes", "status", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        allowed_property_sell_request_ids = PropertySellRequest.objects.filter(
            created_by=request.user
        ).values_list('id', flat=True)

        return qs.filter(id__in=allowed_property_sell_request_ids)
    

admin.site.register(PropertySellRequest,PropertySellRequestAdmin)
