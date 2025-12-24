from django.contrib import admin

# Register your models here.
from django.contrib import admin
from ..models.WorkerTypes import WorkerTypes
from common.filters.adminModelFilter import TableForiegnKeyListFilter

class WorkerTypesAdmin(admin.ModelAdmin):

    list_display = ["name", "wages", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    search_fields = ["name"]
    

admin.site.register(WorkerTypes,WorkerTypesAdmin)
