from django.contrib import admin
from ..models.Cities import Cities
from ..models.Regions import Regions
from common.filters.adminModelFilter import TableForiegnKeyListFilter

class RegionsAdmin(admin.ModelAdmin):

    list_display = ["name", "city_id", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    list_filter = [TableForiegnKeyListFilter("Cities", "city_id", "name", Cities)]
    search_fields = ["name"]
    

admin.site.register(Regions,RegionsAdmin)
