from django.contrib import admin
from ..models.Countries import Countries
      
class CountriesAdmin(admin.ModelAdmin):

    list_display = ["name", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    search_fields = ["name"]
    

admin.site.register(Countries,CountriesAdmin)
