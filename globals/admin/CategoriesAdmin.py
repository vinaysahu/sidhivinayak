from django.contrib import admin
from ..models.Categories import Categories
from ..models.CategoryMedia import CategoryMedia
from ..forms.CategoryMediaForm import CategoryMediaForm
from django.utils.html import format_html
from common.filters.adminModelFilter import SameTableParentFilter

class CategoryMediaInline(admin.TabularInline):
        model = CategoryMedia
        extra = 5
        exclude = ('created_at', 'updated_at')
        verbose_name = "Category Product"
        verbose_name_plural = "Category Product"
        fields = ['file', 'show_media_image']   # 👈 define display order
        readonly_fields = ['show_media_image']

        def show_media_image(self, obj):
            if obj.file:
                return format_html('<img src="{}" width="50" height="50" />', obj.file.url)
            return "—"
        class Media:
            css = {
                'all': ('css/hide_file_path.css',)  # custom CSS load
            }

class CategoriesAdmin(admin.ModelAdmin):

    list_display = ["name","show_name", "parent_id", "show_image", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    def show_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "—"

    show_image.short_description = "Image"

    def show_name(self, obj):
        if obj.parent_id:
            return obj.name+" "+ obj.parent_id.name
        return obj.name
    show_name.short_description = "Name"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent_id":
            if request.resolver_match.kwargs.get('object_id'):
                # current object id jise edit kar rahe hain
                current_obj_id = request.resolver_match.kwargs.get('object_id')
                kwargs["queryset"] = Categories.objects.exclude(id=current_obj_id)
            else:
                kwargs["queryset"] = Categories.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    list_filter = [SameTableParentFilter("Parent Category","parent_id",Categories),"status"]
    search_fields = ["name"]
    inlines = [CategoryMediaInline]
    

admin.site.register(Categories,CategoriesAdmin)
