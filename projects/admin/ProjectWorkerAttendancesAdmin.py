from decimal import Decimal

from django import forms
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

# Fields that are always auto-computed / not user-editable via the
# mark_today_attendance link — shared by both wage-type branches.
_AUTO_EXCLUDE = (
    'project_worker_id', 'total_amount', 'project_id', 'worker_id',
    'remaining_amount', 'working_date', 'created_at', 'updated_at',
    'payment_date',
)


class ProjectWorkerAttendancesAdmin(admin.ModelAdmin):

    change_form_template = "admin/projects/workerAttendance/change_form.html"

    list_display = [
        "get_project_name", "total_amount", "paid_amount",
        "remaining_amount", "hours", "working_date", "payment_date",
    ]

    list_filter = [
        TableForiegnKeyListHasPermissionFilter(
            "Projects", "project_id", "name", Projects, UserProjectPermissions
        ),
        TableForiegnKeyListFilter("Workers", "worker_id", "name", Workers),
    ]

    list_per_page = 15
    list_max_show_all = 100
    list_select_related = True

    def get_project_name(self, obj):
        return format_html(
            "{} ({})", obj.project_worker_id.project_id, obj.project_worker_id.worker_id
        )

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

    def _get_project_worker(self, request):
        pw_id = request.GET.get("project_worker_id")
        if not pw_id:
            return None
        try:
            return ProjectWorkers.objects.select_related('worker_id').get(id=int(pw_id))
        except (ProjectWorkers.DoesNotExist, ValueError):
            return None

    def get_exclude(self, request, obj=None):
        pw = self._get_project_worker(request)
        if pw is None:
            # Normal admin view — exclude only auto-managed / internal fields
            return ('project_worker_id', 'updated_at', 'payment_date')

        if pw.wages_type == ProjectWorkers.WAGES_PER_HOUR:
            # Per Hour: show both `hours` and `paid_amount`
            return _AUTO_EXCLUDE
        else:
            # Per Day / Lum Sum / Per SqFt: show paid_amount, hide hours
            return _AUTO_EXCLUDE + ('hours',)

    def has_add_permission(self, request, obj=None):
        return bool(request.GET.get("project_worker_id"))

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    def get_form(self, request, obj=None, change=False, **kwargs):
        Form = super().get_form(request, obj, change=change, **kwargs)
        pw = self._get_project_worker(request)
        if pw is None:
            return Form

        wages_type = pw.wages_type

        if wages_type in (ProjectWorkers.WAGES_LUM_SUM, ProjectWorkers.WAGES_PER_SQ_FT):
            label = pw.get_wages_type_display()

            class FormWithRequiredAmount(Form):
                def clean_paid_amount(self):
                    amount = self.cleaned_data.get('paid_amount')
                    if not amount or amount <= 0:
                        raise forms.ValidationError(
                            f'Amount field is required for {label} wage type.'
                        )
                    return amount

            return FormWithRequiredAmount

        if wages_type == ProjectWorkers.WAGES_PER_HOUR:
            class FormWithRequiredHours(Form):
                def clean_hours(self):
                    hours = self.cleaned_data.get('hours')
                    if not hours or hours <= 0:
                        raise forms.ValidationError(
                            'Hours field is required and must be greater than 0 '
                            'for Per Hour wage type.'
                        )
                    return hours

            return FormWithRequiredHours

        return Form

    def add_view(self, request, form_url='', extra_context=None):
        """Pass project-worker info to the template for the info card and
        live-calculation JS."""
        extra_context = extra_context or {}
        pw = self._get_project_worker(request)
        if pw:
            extra_context['project_worker'] = pw
            extra_context['is_per_hour'] = (
                pw.wages_type == ProjectWorkers.WAGES_PER_HOUR
            )
            extra_context['is_per_sq_ft'] = (
                pw.wages_type == ProjectWorkers.WAGES_PER_SQ_FT
            )
            if extra_context['is_per_sq_ft']:
                wages = Decimal(str(pw.wages or 0))
                area = Decimal(str(pw.area or 0))
                extra_context['total_contract'] = wages * area

            extra_context['amount_required'] = pw.wages_type in (
                ProjectWorkers.WAGES_LUM_SUM,
                ProjectWorkers.WAGES_PER_SQ_FT,
            )
        return super().add_view(request, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        raw_id = request.GET.get("project_worker_id")
        if not raw_id:
            self.message_user(request, "Project Worker ID missing.", level=messages.ERROR)
            return

        try:
            project_worker_id = int(raw_id)
        except ValueError:
            self.message_user(request, "Invalid Project Worker ID.", level=messages.ERROR)
            return

        try:
            project_worker = ProjectWorkers.objects.get(id=project_worker_id)
        except ProjectWorkers.DoesNotExist:
            self.message_user(request, "Invalid Project Worker ID!", level=messages.ERROR)
            return

        last_entry = (
            ProjectWorkerAttendances.objects
            .filter(project_worker_id=project_worker)
            .last()
        )

        if last_entry and last_entry.working_date == timezone.now().date():
            self.message_user(
                request, "Today Attendance marked already.", level=messages.ERROR
            )
            return

        wages = Decimal(str(project_worker.wages or 0))

        if project_worker.wages_type == ProjectWorkers.WAGES_PER_HOUR:
            hours = obj.hours
            if not hours or hours <= 0:
                self.message_user(
                    request,
                    "Hours field is required and must be greater than 0 for Per Hour wage type.",
                    level=messages.ERROR,
                )
                return
            today_amount = Decimal(str(hours)) * wages
            paid = Decimal(str(obj.paid_amount or 0))
        elif project_worker.wages_type == ProjectWorkers.WAGES_LUM_SUM:
            if not obj.paid_amount or obj.paid_amount <= 0:
                self.message_user(
                    request,
                    f"Amount field is required for {project_worker.get_wages_type_display()} wage type.",
                    level=messages.ERROR,
                )
                return
            today_amount = Decimal(str(obj.paid_amount))
            paid = today_amount
        elif project_worker.wages_type == ProjectWorkers.WAGES_PER_SQ_FT:
            if not obj.paid_amount or obj.paid_amount <= 0:
                self.message_user(
                    request,
                    "Amount field is required for Per SQ FT wage type.",
                    level=messages.ERROR,
                )
                return

            area = Decimal(str(project_worker.area or 0))
            total_contract = wages * area

            if not last_entry:
                today_amount = total_contract
            else:
                # Adjust today_amount so that new_total becomes total_contract
                today_amount = total_contract - Decimal(str(last_entry.total_amount or 0))
                if today_amount < 0:
                    today_amount = Decimal('0')

            paid = Decimal(str(obj.paid_amount))
        else:
            today_amount = wages
            paid = Decimal(str(obj.paid_amount or 0))

        last_total = Decimal(str(last_entry.total_amount)) if last_entry and last_entry.total_amount else Decimal('0')
        last_remain = Decimal(str(last_entry.remaining_amount)) if last_entry and last_entry.remaining_amount else Decimal('0')


        new_total = last_total + today_amount
        new_remaining = (last_remain + today_amount if last_entry else today_amount) - paid

        obj.project_worker_id = project_worker
        obj.total_amount = new_total
        obj.paid_amount = paid
        obj.remaining_amount = new_remaining
        obj.working_date = timezone.now().date()

        super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        pw_id = int(request.GET.get("project_worker_id", 0))
        project_worker = ProjectWorkers.objects.get(id=pw_id)
        return redirect(
            f'/admin/projects/projects/{project_worker.project_id.id}/change/#project-workers-tab'
        )


admin.site.register(ProjectWorkerAttendances, ProjectWorkerAttendancesAdmin)
