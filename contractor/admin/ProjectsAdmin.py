from django.contrib import admin
from ..models.Projects import Projects
from ..models.ProjectWorkers import ProjectWorkers
from django.urls import path, reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.html import format_html

class ProjectWorkersInline(admin.TabularInline):
    model = ProjectWorkers
    extra = 0
    exclude = ('created_at', 'updated_at') 
    max_num = 5  # restrict to max 5 images
    verbose_name = "Project Worker"
    verbose_name_plural = "Project Workers"
    fields = ['mark_today_attendance','worker_id', 'wages_type', 'wages', 'status']   # 👈 define display order
    readonly_fields=['mark_today_attendance']

    def mark_today_attendance(self, obj):
        if not obj or not obj.pk:
            return ""
        edit_url = reverse("admin:contractor_projectworkerattendances_add")
        view_url = reverse("admin:contractor_projectworkerattendances_changelist")
        
        return format_html(
            '<a href="{}?project_worker_id={}" title="Mark Today Attendance"><i class="fa fa-address-card text-black"></i></a> '
            '<a class="ml-2" href="{}?project_id={}&worker_id={}" title="Attendance View"><i class="fa fa-eye text-black"></i></a> ',
            edit_url, obj.id, view_url, obj.project_id.id, obj.worker_id.id
        )
    mark_today_attendance.short_description="Action"
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == "worker_id" and not request.user.is_superuser:
            field.queryset = field.queryset.filter(
                created_by=request.user
            )

        return field

    class Media:
        js = ("admin/projects/projectworker_auto_fill.js",)


class ProjectsAdmin(admin.ModelAdmin):

    list_display = ["name", "project_type", "address", "area_sqyd", "status"] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    search_fields = ["name"]
    list_filter = ["status", "project_type"]

    inlines = [ProjectWorkersInline]
        
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            
            path(
            "worker-attendance/<int:project_id>/",
            self.admin_site.admin_view(self.project_worker_attendance_page),
            name="projects_worker_attendance",
            ),
        ]
        return custom_urls + urls
    
    def project_worker_attendance_page(self, request, project_id):
        project = get_object_or_404(Projects, pk=project_id)
        return render(
            request,
            "admin/projects/worker_attendance.html",
            {"project": project}
        )
    

admin.site.register(Projects,ProjectsAdmin)
