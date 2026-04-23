from django.contrib import admin, messages
from django.urls import path
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import tempfile
from globals.models.Materials import Materials
from globals.models.Suppliers import Suppliers
from ..models.ProjectMaterials import ProjectMaterials
from ..models.ProjectMaterialLists import ProjectMaterialLists
from ..models.Projects import Projects
from projects.models.UserProjectPermissions import UserProjectPermissions
from django.shortcuts import redirect
from common.filters.adminModelFilter import TableForiegnKeyListFilter,TableForiegnKeyListHasPermissionFilter
from django.utils.html import format_html
from common.utils.ocr_utils import extract_text_from_image
from common.utils.bill_parser import extract_bill_data


class ProjectMaterialListsInline(admin.TabularInline):
    model = ProjectMaterialLists
    extra = 2
    exclude = ('created_at', 'updated_at') 
    max_num = 10  # restrict to max 5 images
    verbose_name = "Project Material List"
    verbose_name_plural = "Project Material Lists"
    fields = ['material_id','quantity','unit','rate', 'amount']   # 👈 define display order

      
class ProjectMaterialsAdmin(admin.ModelAdmin):

    list_display = ['project_id', 'supplier_id', 'total_amount', 'balance', 'paid_amount', 'received_date', 'payment_status' ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    # readonly_fields=['project_id']

    inlines = [ProjectMaterialListsInline]


    search_fields = ['total_amount', 'paid_amount','bill_no']
    list_filter = ["payment_status", TableForiegnKeyListHasPermissionFilter("Projects", "project_id","name",Projects,UserProjectPermissions), TableForiegnKeyListFilter("Suppliers", "supplier_id","shop_name",Suppliers)]

    readonly_fields = ['extract_button']

    list_per_page = 15          # ← yeh add karo
    list_max_show_all = 100     # ← yeh add karo
    list_select_related = True

    def extract_button(self, obj):
        

        return format_html(
            '<button type="button" class="button extract-bill-btn" id="id_extract_bill">Extract From Bill</button>'
        )

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

        print("Workinggggggggggggggggg")        
        project_id= request.GET.get("project_id")

        if project_id:
            if not ProjectMaterials.objects.filter(project_id=project_id).exists():
                self.message_user(request, "Invalid Project ID!", level=messages.ERROR)
                return redirect("/admin/projects/projects/")
            
            obj.project_id = ProjectMaterials.objects.get(project_id=project_id)
        
        super().save_model(request, obj, form, change)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'extract-bill-from-image/',
                self.admin_site.admin_view(self.extract_bill_from_image),
                name='extract-bill',
            ),
        ]
        return custom_urls + urls
    
    def extract_bill_from_image(self, request):

        if request.method != "POST":
            return JsonResponse({"error": "Invalid request"}, status=400)

        image_file = request.FILES.get("image")

        if not image_file:
            return JsonResponse({"error": "No image uploaded"}, status=400)

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            for chunk in image_file.chunks():
                tmp.write(chunk)
            temp_path = tmp.name

        raw_text = extract_text_from_image(temp_path)

        data = extract_bill_data(raw_text)

        print("raw_text raw_text raw_text raw_text raw_text: ",data)

        return JsonResponse(data)
    

    class Media:
        js = ('admin/js/billExtract.js',)



admin.site.register(ProjectMaterials,ProjectMaterialsAdmin)
