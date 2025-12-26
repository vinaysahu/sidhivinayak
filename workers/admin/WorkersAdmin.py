from django.contrib import admin

# Register your models here.
from django.contrib import admin
from ..models.Workers import Workers
from ..models.WorkerTypes import WorkerTypes
from common.filters.adminModelFilter import TableForiegnKeyListFilter

class WorkersAdmin(admin.ModelAdmin):

    list_display = ["name", "worker_type_id", "wages_type", "mobile", "wages", "status", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_by','created_at', 'updated_at')       # Remove from FORM

    search_fields = ["name"]
    list_filter = [TableForiegnKeyListFilter("Worker Type", "worker_type_id", "name", WorkerTypes), "wages_type", "status"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        allowed_worker_ids = Workers.objects.filter(
            created_by=request.user
        ).values_list('id', flat=True)

        return qs.filter(id__in=allowed_worker_ids)
    

admin.site.register(Workers,WorkersAdmin)
