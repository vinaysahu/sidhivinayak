from django.contrib import admin, messages
from globals.models.Materials import Materials
from globals.models.Suppliers import Suppliers
from ..models.ProjectMaterials import ProjectMaterials
from django.shortcuts import redirect
from common.filters.adminModelFilter import TableForiegnKeyListFilter
      
class ProjectMaterialsAdmin(admin.ModelAdmin):

    list_display = ['project_id', 'material_id','quantity','unit', 'supplier_id', 'total_amount', 'balance', 'paid_amount', 'received_date', 'payment_status' ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    # readonly_fields=['project_id']

    search_fields = ["unit", 'total_amount','quantity','paid_amount']
    list_filter = ["payment_status", TableForiegnKeyListFilter("Suppliers", "supplier_id","shop_name",Suppliers), TableForiegnKeyListFilter("Materials", "material_id","name",Materials)]

    # def has_module_permission(self, request):
    #     return False
    
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
