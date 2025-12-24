from django.contrib import admin
from ..models.States import States
from ..models.Countries import Countries
from common.filters.adminModelFilter import TableForiegnKeyListFilter
 
class StatesAdmin(admin.ModelAdmin):

    list_display = ["name", "country_id", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    list_filter = [TableForiegnKeyListFilter("Countries", "country_id", "name", Countries)]
    search_fields = ["name"]
    

admin.site.register(States,StatesAdmin)
