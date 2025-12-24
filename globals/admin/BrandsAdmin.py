from django.contrib import admin
from ..models.Brands import Brands
from django.utils.html import format_html
      
class BrandsAdmin(admin.ModelAdmin):

    list_display = ["name", "show_image", "description", "status", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    def show_image(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" />', obj.logo.url)
        return "—"

    show_image.short_description = "Logo"

    list_filter = ["status"]
    search_fields = ["name"]
    

admin.site.register(Brands,BrandsAdmin)
