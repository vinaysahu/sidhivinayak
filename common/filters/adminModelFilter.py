from django.contrib import admin
from django.core.exceptions import ValidationError
import os

def UniqueTableColumnListFilter(field_title, field_name, table):
    class UniqueCapacityFilter(admin.SimpleListFilter):
        title = field_title or field_name.replace("_", " ").title()  # Filter title in sidebar
        parameter_name = field_name  # Query parameter name

        def lookups(self, request, model_admin):
            # Get distinct values from database
            tableData = table.objects.values_list(field_name, flat=True).distinct()
            return [(c, f"{c}") for c in tableData if c is not None]

        def queryset(self, request, queryset):
            if self.value():
                # Dynamic filtering using dictionary unpacking
                return queryset.filter(**{field_name: self.value()})
            return queryset

    return UniqueCapacityFilter

def TableForiegnKeyListFilter(field_title, field_name, parent_field_name, table):
    class ForiegnKeyFilter(admin.SimpleListFilter):
        title = field_title or field_name.replace("_", " ").title()
        parameter_name = field_name

        def lookups(self, request, model_admin):
            tableDatas = table.objects.all()
            return [(tableData.id, getattr(tableData, parent_field_name)) for tableData in tableDatas]

        def queryset(self, request, queryset):
            if self.value():
                # IMPORTANT: Actual filtering
                filter_kwargs = {field_name: self.value()}
                return queryset.filter(**filter_kwargs)
            return queryset

    return ForiegnKeyFilter


def SameTableParentFilter(field_title, field_name, table):
    class ParentCategoryFilter(admin.SimpleListFilter):
        title = field_title or field_name.replace("_", " ").title()  # Filter title in sidebar
        parameter_name = field_name  # Query parameter name
        

        def lookups(self, request, model_admin):
            # Add a placeholder-like first option manually
            categories = table.objects.filter(**{f"{field_name}__isnull": True})
            lookups = [(cat.id, cat.name) for cat in categories]
            return lookups

        def queryset(self, request, queryset):
            if self.value():
                return queryset.filter(**{field_name: self.value()})
            return queryset
    
    return ParentCategoryFilter

def validate_image_size(image):
    if int(image.size) > 600 * 1024:  # 600 KB
        raise ValidationError("Image size should not exceed 600KB.")

def validate_image_format(image):
    ext = os.path.splitext(image.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png']
    if ext not in valid_extensions:
        raise ValidationError("Only JPG, JPEG, and PNG formats are allowed.")

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.avi', '.mkv', '.pdf']

    if ext not in allowed_extensions:
        raise ValidationError(f"Unsupported file type: {ext}. Allowed: {allowed_extensions}")
