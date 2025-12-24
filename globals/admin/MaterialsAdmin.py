from django.contrib import admin
from ..models.Materials import Materials
      
class MaterialsAdmin(admin.ModelAdmin):

    list_display = ["name", "description", "status", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM


    list_filter = ["status"]
    search_fields = ["name"]
    

admin.site.register(Materials,MaterialsAdmin)
