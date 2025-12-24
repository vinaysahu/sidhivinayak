from django.contrib import admin

# Register your models here.
from django.contrib import admin
from ..models.Workers import Workers
from ..models.WorkerTypes import WorkerTypes
from common.filters.adminModelFilter import TableForiegnKeyListFilter

class WorkersAdmin(admin.ModelAdmin):

    list_display = ["name", "worker_type_id", "wages_type", "mobile", "wages", "status", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    search_fields = ["name"]
    list_filter = [TableForiegnKeyListFilter("Worker Type", "worker_type_id", "name", WorkerTypes), "wages_type", "status"]
    

admin.site.register(Workers,WorkersAdmin)
