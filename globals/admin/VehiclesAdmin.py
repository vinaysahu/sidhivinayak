from django.contrib import admin
from ..models.Vehicles import Vehicles
from django.utils.html import format_html
from common.filters.adminModelFilter import UniqueTableColumnListFilter

class VehiclesAdmin(admin.ModelAdmin):

    list_display = ["name", "reg_number", "model", "capacity_tons", "status", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    def show_image(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" />', obj.logo.url)
        return "—"

    show_image.short_description = "Logo"

    list_filter = ["status",UniqueTableColumnListFilter("Capacity (Tons)","capacity_tons",Vehicles)]
    search_fields = ["name", "reg_number"]
    

admin.site.register(Vehicles,VehiclesAdmin)
