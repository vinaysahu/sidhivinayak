from django.contrib import admin, messages
from ..models.ProjectWorkerAttendances import ProjectWorkerAttendances
from ..models.Projects import Projects
from ..models.ProjectWorkers import ProjectWorkers
from workers.models.Workers import Workers
from projects.models.UserProjectPermissions import UserProjectPermissions
from django.shortcuts import redirect
from common.filters.adminModelFilter import TableForiegnKeyListFilter, TableForiegnKeyListHasPermissionFilter
from django.utils.html import format_html
from django.utils import timezone

class ProjectWorkerAttendancesAdmin(admin.ModelAdmin):

    change_form_template = "admin/projects/workerAttendance/change_form.html"

    list_display = ["get_project_name", "total_amount", "paid_amount", "remaining_amount", "working_date" ] # grid mae kaisa view
    # exclude = ('project_worker_id', 'total_amount', 'project_id', 'worker_id', 'remaining_amount', 'working_date', 'created_at', 'updated_at')       # Remove from FORM

    # search_fields = ["plot_no"]
    list_filter = [TableForiegnKeyListHasPermissionFilter("Projects", "project_id","name",Projects,UserProjectPermissions), TableForiegnKeyListFilter("Workers", "worker_id","name",Workers)]

    def get_project_name(self, obj):
        return format_html("{} ({})",obj.project_worker_id.project_id,obj.project_worker_id.worker_id)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        allowed_project_ids = UserProjectPermissions.objects.filter(
            user=request.user
        ).values_list('projects__id', flat=True)

        if not allowed_project_ids:
            return qs

        return qs.filter(project_id__id__in=allowed_project_ids)
    
    def get_exclude(self, request, obj=None):

        # Default exclude
        default_exclude = (
            'project_worker_id',
            'updated_at'
        )

        # Agar URL me ?exclude=yes ho
        if request.GET.get("project_worker_id"):
            return (
                'project_worker_id', 'total_amount', 'project_id', 'worker_id', 'remaining_amount', 'working_date', 'created_at', 'updated_at'
            )

        return default_exclude
    
    def has_add_permission(self, request, obj=None):
        if request.GET.get("project_worker_id"):
            return True
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True
    
    def save_model(self, request, obj, form, change):
        
        project_workerId= int(request.GET.get("project_worker_id"))

        hasError = False

        if project_workerId:
            if not ProjectWorkers.objects.filter(id=project_workerId).exists():
                self.message_user(request, "Invalid Project Worker ID!", level=messages.ERROR)
                hasError = True
                
            projectWorker = ProjectWorkers.objects.get(id=project_workerId)
            projectWorkerLastEntry = ProjectWorkerAttendances.objects.filter(project_worker_id=projectWorker).last()

            if projectWorkerLastEntry and projectWorkerLastEntry.working_date == timezone.now().date():
                self.message_user(request, "Today Attendance marked already.", level=messages.ERROR)
                hasError = True

            paid = obj.paid_amount or 0
            wages = projectWorker.wages or 0

            # NONE SAFE VALUES
            last_total = projectWorkerLastEntry.total_amount if projectWorkerLastEntry and projectWorkerLastEntry.total_amount else 0
            last_remain = projectWorkerLastEntry.remaining_amount if projectWorkerLastEntry and projectWorkerLastEntry.remaining_amount else 0

            # NEW VALUES
            total_amount = last_total + wages
            remaining_amount = (last_remain + wages if projectWorkerLastEntry else wages) - paid
            
            obj.project_worker_id = projectWorker
            obj.total_amount = total_amount
            obj.remaining_amount = remaining_amount
            obj.working_date = timezone.now().date()

        if not hasError:
            super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):  # yae code model save hone k baad mae chlta hai
        project_workerId= int(request.GET.get("project_worker_id"))
        projectWorker = ProjectWorkers.objects.get(id=project_workerId)
        return redirect(f'/admin/projects/projects/{projectWorker.project_id.id}/change/#project-workers-tab')


admin.site.register(ProjectWorkerAttendances,ProjectWorkerAttendancesAdmin)
