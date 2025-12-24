from django.contrib import admin
from ..models.PropertySellRequest import PropertySellRequest
      
class PropertySellRequestAdmin(admin.ModelAdmin):

    list_display = [ "owner_name", "phone_no", "alt_phone_no", "email", "address", "area_sqyd", "dimension", "expected_price", "reason_for_selling", "notes", "status", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM
    

admin.site.register(PropertySellRequest,PropertySellRequestAdmin)
