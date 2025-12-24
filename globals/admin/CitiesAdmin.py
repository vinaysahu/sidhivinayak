from django.contrib import admin
from ..models.Cities import Cities
from ..models.States import States
from common.filters.adminModelFilter import TableForiegnKeyListFilter

class CitiesAdmin(admin.ModelAdmin):

    list_display = ["name", "state_id", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    list_filter = [TableForiegnKeyListFilter("States", "state_id", "name", States)]
    search_fields = ["name"]
    

admin.site.register(Cities,CitiesAdmin)
