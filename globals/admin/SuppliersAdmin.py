from django.contrib import admin
from ..models.Brands import Brands
from ..models.Suppliers import Suppliers
from django.utils.html import format_html
from common.filters.adminModelFilter import TableForiegnKeyListFilter

class SuppliersAdmin(admin.ModelAdmin):

    list_display = ["shop_name", "brand_id", "show_image", "first_name", "last_name", "mobile", "status", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    def show_image(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" />', obj.logo.url)
        return "—"

    show_image.short_description = "Logo"

    list_filter = [TableForiegnKeyListFilter("Brands", "brand_id", "name", Brands),"status"]
    search_fields = ["shop_name"]
    

admin.site.register(Suppliers,SuppliersAdmin)
