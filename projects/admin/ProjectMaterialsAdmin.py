from django.contrib import admin, messages
from globals.models.Materials import Materials
from globals.models.Suppliers import Suppliers
from ..models.ProjectMaterials import ProjectMaterials
from ..models.Projects import Projects
from projects.models.UserProjectPermissions import UserProjectPermissions
from django.shortcuts import redirect
from common.filters.adminModelFilter import TableForiegnKeyListFilter,TableForiegnKeyListHasPermissionFilter
      
class ProjectMaterialsAdmin(admin.ModelAdmin):

    list_display = ['project_id', 'material_id','quantity','unit', 'supplier_id', 'total_amount', 'balance', 'paid_amount', 'received_date', 'payment_status' ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    # readonly_fields=['project_id']

    search_fields = ["unit", 'total_amount','quantity','paid_amount']
    list_filter = ["payment_status", TableForiegnKeyListHasPermissionFilter("Projects", "project_id","name",Projects,UserProjectPermissions), TableForiegnKeyListFilter("Suppliers", "supplier_id","shop_name",Suppliers), TableForiegnKeyListFilter("Materials", "material_id","name",Materials)]

    # def has_module_permission(self, request):
    #     return False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == "project_id" and not request.user.is_superuser:
            allowed_project_ids = UserProjectPermissions.objects.filter(
                user=request.user
            ).values_list('projects__id', flat=True)

            if allowed_project_ids:
                field.queryset = field.queryset.filter(
                    id__in = allowed_project_ids
                )
            print("allowed_project_ids", allowed_project_ids)
            print("field", field.queryset)

        return field

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
    
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        project_id = request.GET.get("project_id")
        
        if project_id:  # update mode
            # update page me project_id field hide karo
            
            if not ProjectMaterials.objects.filter(project_id=project_id).exists():
                self.message_user(request, "Invalid Project ID!", level=messages.ERROR)
                return redirect("/admin/projects/projects/")
            
            fields.remove("project_id")

        return fields
    
    def save_model(self, request, obj, form, change):
        
        project_id= request.GET.get("project_id")

        if project_id:
            if not ProjectMaterials.objects.filter(project_id=project_id).exists():
                self.message_user(request, "Invalid Project ID!", level=messages.ERROR)
                return redirect("/admin/projects/projects/")
            
            obj.project_id = ProjectMaterials.objects.get(project_id=project_id)
        
        super().save_model(request, obj, form, change)
    
    

admin.site.register(ProjectMaterials,ProjectMaterialsAdmin)
