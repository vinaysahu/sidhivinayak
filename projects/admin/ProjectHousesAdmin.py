from django.contrib import admin, messages
from ..models.Projects import Projects
from ..models.ProjectHouses import ProjectHouses
from projects.models.UserProjectPermissions import UserProjectPermissions
from django.urls import path
from django.shortcuts import redirect
from django.urls import resolve
from common.filters.adminModelFilter import TableForiegnKeyListHasPermissionFilter
      
class ProjectHousesAdmin(admin.ModelAdmin):

    list_display = ["plot_no", "area_sqyd", "builtup_area_sqft", "dimension", "bedrooms", "bathrooms", "Kitchen", "balconies", "parking", "total_floors", "price", "house_images", "layout", "complete_percentage", "status" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    # readonly_fields=['project_id']

    search_fields = ["plot_no"]
    list_filter = ["status", TableForiegnKeyListHasPermissionFilter("Projects", "project_id","name",Projects,UserProjectPermissions)]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == "project_id" and not request.user.is_superuser:
            allowed_project_ids = UserProjectPermissions.objects.filter(
                user=request.user
            ).values_list('projects__id', flat=True)

            if allowed_project_ids:
                field.queryset = field.queryset.filter(
                    id__in=allowed_project_ids
                )

        return field

    # def has_module_permission(self, request):
    #     return False

    # override default admin URLs
    # def get_urls(self):
    #     original_urls = super().get_urls()

    #     custom_urls = [
    #         # path(
    #         #     '/',
    #         #     self.admin_site.admin_view(self.changelist_view),
    #         #     name='projecthouses_changelist',
    #         # ),
    #         # path(
    #         #     'add/',
    #         #     self.admin_site.admin_view(self.add_view),
    #         #     name='projecthouses_add',
    #         # ),
    #         # path(
    #         #     '<path:object_id>/change',
    #         #     self.admin_site.admin_view(self.change_view),
    #         #     name='projecthouses_change',
    #         # ),
    #     ]

    #     return custom_urls + original_urls

    # Force project_id required  
    # def changelist_view(self, request, project_id=None, extra_context=None):
        
    #     if not project_id:
    #         return redirect("/admin/projects/projects/")
    #     request.project_id = project_id
    #     return super().changelist_view(request, extra_context)

    # def add_view(self, request, project_id=None, extra_context=None):
        
    #     # if not project_id:
    #     #     return redirect("/admin/projects/projects/")
    #     request.project_id = project_id
    #     return super().add_view(request, extra_context)

    # def change_view(self, request, object_id, *args, **kwargs):
    #     project_id = kwargs.get("project_id")
    #     if not project_id:
    #         return redirect("/admin/projects/projects/")
    #     request.project_id = project_id
    #     return super().change_view(request, object_id, *args, **kwargs)
    
    # def response_add(self, request, obj, post_url_continue=None):
    #     project_id = getattr(request, "project_id", None)

    #     if "_continue" in request.POST:
    #         return redirect(f"../{obj.id}/change/{project_id}")

    #     return redirect(f"/admin/projects/projecthouses/{project_id}/")


    # def response_change(self, request, obj):
    #     project_id = getattr(request, "project_id", None)

    #     if "_continue" in request.POST:
    #         return redirect(f"../../{obj.id}/change/{project_id}")

    #     return redirect(f"/admin/projects/projecthouses/{project_id}/")

    # def add_view(self, request, extra_context=None):
    #     project_id = request.GET.get("project_id")

    #     # redirect before page loads
    #     if not project_id or not Projects.objects.filter(id=project_id).exists():
    #         self.message_user(request, "Invalid Project ID!", level=messages.ERROR)
    #         return redirect("/admin/projects/projects/")

    #     return super().add_view(request, extra_context)
    
    # def get_form(self, request, obj=None, **kwargs):
    #     form = super().get_form(request, obj, **kwargs)
    #     project_id = request.GET.get("project_id")

    #     # Only add form
    #     if obj is None and project_id:
    #         if Projects.objects.filter(id=project_id).exists():
    #             if "project_id" in form.base_fields:
    #                 form.base_fields.pop("project_id")

    #     return form
    
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        project_id = request.GET.get("project_id")
        
        if project_id:  # update mode
            # update page me project_id field hide karo
            
            if not Projects.objects.filter(id=project_id).exists():
                self.message_user(request, "Invalid Project ID!", level=messages.ERROR)
                return redirect("/admin/projects/projects/")
            
            fields.remove("project_id")

        return fields
    
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
    
    def save_model(self, request, obj, form, change):
        
        project_id= request.GET.get("project_id")

        if project_id:
            if not Projects.objects.filter(id=project_id).exists():
                self.message_user(request, "Invalid Project ID!", level=messages.ERROR)
                return redirect("/admin/projects/projects/")
            
            obj.project_id = Projects.objects.get(id=project_id)
        
        super().save_model(request, obj, form, change)
    
    # def get_readonly_fields(self, request, obj=None):
    #     if obj is None:  # Only in ADD form
    #         return ['project_id']
    #     return []
    
# _original_each_context = admin.AdminSite.each_context

# def custom_each_context(self, request):
#     context = _original_each_context(self, request)

#     # Current URL resolver
#     resolver = resolve(request.path)

#     # If current admin view belongs to ProjectHouses
#     if resolver.app_name == "projecthouses":  # <-- Change the app label
#         context["active_app"] = "projects"    # <-- Sidebar target app label

#     return context

# admin.AdminSite.each_context = custom_each_context

admin.site.register(ProjectHouses,ProjectHousesAdmin)
