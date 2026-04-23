from django.contrib import admin
from ..models.Projects import Projects
from ..models.ProjectAmenities import ProjectAmenities
from ..models.ProjectWorkers import ProjectWorkers
from ..models.ProjectHouses import ProjectHouses
from ..models.ProjectMedia import ProjectMedia
from ..models.ProjectMaterials import ProjectMaterials
from ..models.UserProjectPermissions import UserProjectPermissions
from ..models.ProjectLedger import ProjectLedger
from ..models.ProjectSupplierLedger import ProjectSupplierLedger
from django.urls import path, reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.html import format_html
from django.db.models import Sum
from accounts.utils import format_indian_currency

# ... (Inlines remain unchanged) ...
class ProjectAmenitiesInline(admin.TabularInline):
    model = ProjectAmenities
    extra = 1
    exclude = ('created_at', 'updated_at') 
    max_num = 25
    verbose_name = "Project Amenities"
    verbose_name_plural = "Project Amenities"
    fields = ['amenity_id']

class ProjectMediaInline(admin.TabularInline):
    model = ProjectMedia
    extra = 1
    exclude = ('created_at', 'updated_at') 
    max_num = 5
    verbose_name = "Project Gallery"
    verbose_name_plural = "Project Gallery"
    fields = ['name','file','preview','type']
    readonly_fields =['preview','type']

    def preview(self, obj):
        if not obj or not obj.pk or not obj.file:
            return ""
        url = obj.file.url
        ext = obj.file.name.split('.')[-1].lower()
        if ext in ['jpg', 'jpeg', 'png', 'gif']:
            return format_html('<img src="{}" width="120" style="border-radius:6px;" />',url)
        if ext in ['mp4', 'mov', 'avi', 'mkv']:
            return format_html('<video width="200" controls><source src="{}" type="video/mp4"></video>',url)
        if ext == 'pdf':
            return format_html('<a href="{}" target="_blank" style="padding:6px 12px; background:#007bff; color:white; border-radius:4px; text-decoration:none;">Open PDF</a>',url)
        return "Preview not available"
    preview.short_description = "Preview"

class ProjectMaterialsInline(admin.TabularInline):
    model = ProjectMaterials
    extra = 1
    exclude = ('created_at', 'updated_at') 
    max_num = 1
    verbose_name = "Project Material"
    verbose_name_plural = "Project Materials"
    fields = ['sub_total', 'gst', 'total_amount', 'supplier_id', 'paid_amount']
    def has_add_permission(self, request, obj=None): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return True

class ProjectSupplierLedgerInline(admin.TabularInline):
    model = ProjectSupplierLedger
    extra = 0
    can_delete = False
    show_change_link = False
    verbose_name = 'Supplier Ledger'
    verbose_name_plural = 'Project Supplier Ledger'

    fields = [
        'supplier',
        'item_description',
        'formatted_total',
        'formatted_paid',
        'formatted_balance',
        'balance_status',
        'edit_action',
    ]

    readonly_fields = [
        'supplier',
        'item_description',
        'formatted_total',
        'formatted_paid',
        'formatted_balance',
        'balance_status',
        'edit_action',
    ]

    def formatted_total(self, obj):
        return format_indian_currency(obj.total_amount)
    formatted_total.short_description = "Total"

    def formatted_paid(self, obj):
        return format_indian_currency(obj.paid_amount)
    formatted_paid.short_description = "Paid"

    def formatted_balance(self, obj):
        balance = obj.balance or 0
        color = "red" if balance > 0 else "green"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, format_indian_currency(balance))
    formatted_balance.short_description = "Balance"

    def balance_status(self, obj):
        balance = obj.balance or 0
        if balance > 0:
            return format_html('<span style="color: red; font-weight: bold;">🔴 Baaki hai</span>')
        return format_html('<span style="color: green; font-weight: bold;">🟢 Paid</span>')
    balance_status.short_description = "Status"

    def edit_action(self, obj):
        if obj and obj.pk:
            url = reverse('admin:projects_projectsupplierledger_change', args=[obj.pk])
            return format_html(
                '<a href="{}" class="button" '
                'style="background:#1a56db;color:white;padding:5px 12px;'
                'border-radius:4px;text-decoration:none;font-size:12px;'
                'white-space:nowrap;">✏ Edit</a>',
                url
            )
        return '-'
    edit_action.short_description = 'Action'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('supplier', 'project')

class ProjectWorkersInline(admin.TabularInline):
    model = ProjectWorkers
    extra = 0
    exclude = ('created_at', 'updated_at') 
    max_num = 5
    verbose_name = "Project Worker"
    verbose_name_plural = "Project Workers"
    fields = ['mark_today_attendance','worker_id', 'wages_type', 'wages', 'status']
    readonly_fields=['mark_today_attendance']
    def mark_today_attendance(self, obj):
        if not obj or not obj.pk: return "-"
        edit_url = reverse("admin:projects_projectworkerattendances_add")
        view_url = reverse("admin:projects_projectworkerattendances_changelist")
        return format_html('<a href="{}?project_worker_id={}" title="Mark Today Attendance"><i class="fa fa-address-card text-black"></i></a> <a class="ml-2" href="{}?project_id={}&worker_id={}" title="Attendance View"><i class="fa fa-eye text-black"></i></a> ', edit_url, obj.id, view_url, obj.project_id.id, obj.worker_id.id)
    mark_today_attendance.short_description="Action"

class ProjectHouseInline(admin.TabularInline):
    model = ProjectHouses
    extra = 1
    exclude = ('created_at', 'updated_at') 
    max_num = 5
    verbose_name = "Project Houses"
    verbose_name_plural = "Project House"
    fields = ['get_house_edit_action_list','plot_no','area_sqyd','total_floors','bedrooms', 'bathrooms', 'Kitchen', 'balconies', 'parking', 'price','status','get_house_duplicate_action_list']
    readonly_fields= ['get_house_edit_action_list','get_house_duplicate_action_list']
    def get_house_edit_action_list(self, obj):
        if not obj or not obj.pk: return ""
        edit_url = reverse("admin:projects_projecthouses_change", args=[obj.id])
        return format_html('<a href="{}?project_id={}" title="Edit"><i class="fa fa-edit text-green"></i></a> ', edit_url, obj.project_id.id)
    get_house_edit_action_list.short_description="Actions"
    def get_house_duplicate_action_list(self, obj):
        if not obj or not obj.pk: return ""
        duplicate_url = reverse("admin:projecthouse_duplicate", args=[obj.id])
        if obj.status == ProjectHouses.STATUS_AVAILABLE:
            return format_html('<a href="{}" title="Duplicate"><i class="fa fa-copy text-blue"></i></a>', duplicate_url)
        return ""
    get_house_duplicate_action_list.short_description="Create Duplicate"
    def has_add_permission(self, request, obj=None): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return True
      
class ProjectsAdmin(admin.ModelAdmin):

    change_form_template = "admin/projects/projects/change_form.html"

    list_display = ["name", "project_type", "locality_id", "address", "area_sqyd", "status", "get_action_list" ]
    exclude = ('created_at', 'updated_at')

    inlines = [ProjectAmenitiesInline, ProjectMediaInline, ProjectWorkersInline, ProjectHouseInline, ProjectSupplierLedgerInline]

    search_fields = ["name"]
    list_filter = ["status", "project_type"]
    
    readonly_fields = ['expense_summary']

    list_per_page = 15          # ← yeh add karo
    list_max_show_all = 100     # ← yeh add karo
    list_select_related = True

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        
        # Button 1 - Add House URL
        extra_context['add_house_url'] = f"/admin/projects/projecthouses/add/?project_id={object_id}"
        
        # Button 2 - View Details URL  
        extra_context['view_details_url'] = f"/admin/projects/projects/{object_id}/detail/"
        
        # Button 3 - Worker Attendances URL
        extra_context['worker_attendance_url'] = f"/admin/projects/projectworkerattendances/?project_id={object_id}"
        
        return super().change_view(
            request, object_id, form_url,
            extra_context=extra_context
        )

    def expense_summary(self, obj):
        if not obj or not obj.pk:
            return "Save the project first to see summary."
        
        # Supplier Payments from Ledger
        supplier_pay = ProjectLedger.objects.filter(
            project=obj, entry_type=ProjectLedger.SUPPLIER_PAYMENT
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Worker Payments from Ledger
        worker_pay = ProjectLedger.objects.filter(
            project=obj, entry_type=ProjectLedger.WORKER_PAYMENT
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Pending Supplier Balance
        supplier_pending = ProjectSupplierLedger.objects.filter(
            project=obj
        ).aggregate(total=Sum('balance'))['total'] or 0
        
        total_exp = supplier_pay + worker_pay

        return render(None, 'admin/projects/projects/expense_summary.html', {
            'supplier_pay': format_indian_currency(supplier_pay),
            'worker_pay': format_indian_currency(worker_pay),
            'total_exp': format_indian_currency(total_exp),
            'supplier_pending': format_indian_currency(supplier_pending),
        }).content.decode('utf-8')
    
    expense_summary.short_description = "Project Expense Summary"

    def get_action_list(self, obj):
        if not obj or not obj.pk: return ""
        custom_url = reverse("admin:project_detail", args=[obj.id])
        return format_html('<a href="{}" title="View"><i class="fa fa-eye text-green"></i></a>', custom_url)
    get_action_list.short_description="Actions"
        
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser: return qs
        allowed_project_ids = UserProjectPermissions.objects.filter(user=request.user).values_list('projects__id', flat=True)
        if not allowed_project_ids: return qs
        return qs.filter(id__in=allowed_project_ids)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("<int:object_id>/detail/", self.admin_site.admin_view(self.project_detail_view), name="project_detail"),
            path("<path:object_id>/view/", self.admin_site.admin_view(self.project_view_page), name="project_view"),
            path("duplicate-house/<int:house_id>/", self.admin_site.admin_view(self.duplicate_house), name="projecthouse_duplicate"),
            path("worker-attendance/<int:project_id>/", self.admin_site.admin_view(self.project_worker_attendance_page), name="projects_worker_attendance"),
        ]
        return custom_urls + urls
    
    def duplicate_house(self, request, house_id):
        original = get_object_or_404(ProjectHouses, pk=house_id)
        original.pk = None
        original.save()
        self.message_user(request, "House duplicated successfully!")
        return redirect(f"/admin/projects/projects/{original.project_id.id}/change/#project-house-tab")
    
    def project_detail_view(self, request, object_id):
        project = get_object_or_404(Projects, pk=object_id)
        
        # Gallery
        gallery = ProjectMedia.objects.filter(project_id=project, type=1)
        
        # Workers
        workers = ProjectWorkers.objects.filter(project_id=project).select_related('worker_id', 'worker_id__worker_type_id')
        
        # Houses
        houses = ProjectHouses.objects.filter(project_id=project).select_related('customer_id')
        
        # Financial Summary
        ledger_entries = ProjectLedger.objects.filter(project=project)
        total_supplier_pay = ledger_entries.filter(entry_type=ProjectLedger.SUPPLIER_PAYMENT).aggregate(Sum('amount'))['amount__sum'] or 0
        total_worker_pay = ledger_entries.filter(entry_type=ProjectLedger.WORKER_PAYMENT).aggregate(Sum('amount'))['amount__sum'] or 0
        total_other_exp = ledger_entries.filter(entry_type=ProjectLedger.OTHER_EXPENSE).aggregate(Sum('amount'))['amount__sum'] or 0
        total_expenses = total_supplier_pay + total_worker_pay + total_other_exp
        
        context = {
            **self.admin_site.each_context(request),
            "project": project,
            "gallery": gallery,
            "workers": workers,
            "houses": houses,
            "total_supplier_pay": format_indian_currency(total_supplier_pay),
            "total_worker_pay": format_indian_currency(total_worker_pay),
            "total_other_exp": format_indian_currency(total_other_exp),
            "total_expenses": format_indian_currency(total_expenses),
            "title": f"Project Detail: {project.name}",
            "object_id": object_id,
        }
        return render(request, "admin/projects/projects/detail.html", context)

    def project_view_page(self, request, object_id):
        project = get_object_or_404(Projects, pk=object_id)
        return render(request, "admin/projects/project_view.html", {
            "project": project,
            "projectAmenities": ProjectAmenities.objects.filter(project_id=object_id).all(),
            "projectMedias": ProjectMedia.objects.filter(project_id=object_id).all(),
            "projectWorkers": ProjectWorkers.objects.filter(project_id=object_id).all(),
            "projectHouses": ProjectHouses.objects.filter(project_id=object_id).all()
        })
    
    def project_worker_attendance_page(self, request, project_id):
        project = get_object_or_404(Projects, pk=project_id)
        return render(request, "admin/projects/worker_attendance.html", {"project": project})

admin.site.register(Projects,ProjectsAdmin)
