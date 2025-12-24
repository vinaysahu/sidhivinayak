from django.contrib import admin
from ..models.Projects import Projects
from ..models.ProjectAmenities import ProjectAmenities
from ..models.ProjectWorkers import ProjectWorkers
from ..models.ProjectHouses import ProjectHouses
from ..models.ProjectMedia import ProjectMedia
from ..models.ProjectMaterials import ProjectMaterials
from django.urls import path, reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.html import format_html

class ProjectAmenitiesInline(admin.TabularInline):
    model = ProjectAmenities
    extra = 1
    exclude = ('created_at', 'updated_at') 
    max_num = 25  # restrict to max 5 images
    verbose_name = "Project Amenities"
    verbose_name_plural = "Project Amenities"
    fields = ['amenity_id']   # 👈 define display order

class ProjectMediaInline(admin.TabularInline):
    model = ProjectMedia
    extra = 1
    exclude = ('created_at', 'updated_at') 
    max_num = 5  # restrict to max 5 images
    verbose_name = "Project Gallery"
    verbose_name_plural = "Project Gallery"
    fields = ['name','file','preview','type']   # 👈 define display order
    readonly_fields =['preview','type']

    def preview(self, obj):
        if not obj.file:
            return "No file"

        url = obj.file.url
        ext = obj.file.name.split('.')[-1].lower()

        # Image Preview
        if ext in ['jpg', 'jpeg', 'png', 'gif']:
            return format_html(f'<img src="{url}" width="120" style="border-radius:6px;" />')

        # Video Preview
        if ext in ['mp4', 'mov', 'avi', 'mkv']:
            return format_html(f'''
                <video width="200" controls>
                    <source src="{url}" type="video/mp4">
                </video>
            ''')

        # PDF Preview
        if ext == 'pdf':
            return format_html(f'''
                <a href="{url}" target="_blank" style="padding:6px 12px; background:#007bff; color:white; border-radius:4px; text-decoration:none;">
                    Open PDF
                </a>
            ''')

        return "Preview not available"

    preview.short_description = "Preview"

class ProjectMaterialsInline(admin.TabularInline):
    model = ProjectMaterials
    extra = 1
    exclude = ('created_at', 'updated_at') 
    max_num = 1  # restrict to max 5 images
    verbose_name = "Project Material"
    verbose_name_plural = "Project Materials"
    fields = ['material_id','quantity','unit','total_amount', 'supplier_id', 'paid_amount']   # 👈 define display order

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

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
        edit_url = reverse("admin:projects_projectworkerattendances_add")
        view_url = reverse("admin:projects_projectworkerattendances_changelist")
        
        return format_html(
            '<a href="{}?project_worker_id={}" title="Mark Today Attendance"><i class="fa fa-address-card text-black"></i></a> '
            '<a class="ml-2" href="{}?project_id={}&worker_id={}" title="Attendance View"><i class="fa fa-eye text-black"></i></a> ',
            edit_url, obj.id, view_url, obj.project_id.id, obj.worker_id.id
        )
    mark_today_attendance.short_description="Action"

    class Media:
        js = ("admin/projects/projectworker_auto_fill.js",)

class ProjectHouseInline(admin.TabularInline):
    model = ProjectHouses
    extra = 1
    exclude = ('created_at', 'updated_at') 
    max_num = 5  # restrict to max 5 images
    verbose_name = "Project Houses"
    verbose_name_plural = "Project House"
    fields = ['get_house_edit_action_list','plot_no','area_sqyd','total_floors','bedrooms', 'bathrooms', 'Kitchen', 'balconies', 'parking', 'price','status','get_house_duplicate_action_list']   # 👈 define display order
    readonly_fields= ['get_house_edit_action_list','get_house_duplicate_action_list']
    
    def get_house_edit_action_list(self, obj):
        edit_url = reverse("admin:projects_projecthouses_change", args=[obj.id])

        return format_html(
            '<a href="{}?project_id={}" title="Edit"><i class="fa fa-edit text-green"></i></a> ',
            edit_url, obj.project_id.id
        )
    get_house_edit_action_list.short_description="Actions"

    def get_house_duplicate_action_list(self, obj):
        duplicate_url = reverse("admin:projecthouse_duplicate", args=[obj.id])

        if obj.status == ProjectHouses.STATUS_AVAILABLE:
            return format_html(
                '<a href="{}" title="Duplicate"><i class="fa fa-copy text-blue"></i></a>',
                duplicate_url
            )
        return ""
    get_house_duplicate_action_list.short_description="Create Duplicate"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True
      
class ProjectsAdmin(admin.ModelAdmin):

    change_form_template = "admin/projects/project_change_form.html"

    list_display = ["name", "project_type", "locality_id", "address", "area_sqyd", "status", "get_action_list" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    inlines = [ProjectAmenitiesInline, ProjectMediaInline, ProjectWorkersInline, ProjectHouseInline, ProjectMaterialsInline]

    search_fields = ["name"]
    list_filter = ["status", "project_type"]

    def get_action_list(self, obj):
        custom_url = reverse(
            "admin:project_view",
            args=[obj.id]
        )
        return format_html('<a href="{}" title="View"><i class="fa fa-eye text-green"></i></a>', custom_url)
    get_action_list.short_description="Actions"
        

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/view/",
                self.admin_site.admin_view(self.project_view_page),
                name="project_view",
            ),
            path(
            "duplicate-house/<int:house_id>/",
            self.admin_site.admin_view(self.duplicate_house),
            name="projecthouse_duplicate",
            ),
            path(
            "worker-attendance/<int:project_id>/",
            self.admin_site.admin_view(self.project_worker_attendance_page),
            name="projects_worker_attendance",
            ),
        ]
        return custom_urls + urls
    
    def duplicate_house(self, request, house_id):
        original = get_object_or_404(ProjectHouses, pk=house_id)

        # Create copy
        original.pk = None  # remove ID
        original.plot_no = original.plot_no  # optional: change plot no
        original.save()

        self.message_user(request, "House duplicated successfully!")

        # Redirect back to the project view page
        return redirect(f"/admin/projects/projects/{original.project_id.id}/change/#project-house-tab")
    
    def project_view_page(self, request, object_id):
        project = get_object_or_404(Projects, pk=object_id)
        projectAmenities = ProjectAmenities.objects.filter(project_id=object_id).all()
        projectMedias = ProjectMedia.objects.filter(project_id=object_id).all()
        projectWorkers = ProjectWorkers.objects.filter(project_id=object_id).all()
        projectHouses = ProjectHouses.objects.filter(project_id=object_id).all()
        return render(
            request,
            "admin/projects/project_view.html",
            {
                "project": project,
                "projectAmenities": projectAmenities,
                "projectMedias": projectMedias,
                "projectWorkers": projectWorkers,
                "projectHouses": projectHouses
            }
        )
    
    def project_worker_attendance_page(self, request, project_id):
        project = get_object_or_404(Projects, pk=project_id)
        return render(
            request,
            "admin/projects/worker_attendance.html",
            {"project": project}
        )
    

admin.site.register(Projects,ProjectsAdmin)
