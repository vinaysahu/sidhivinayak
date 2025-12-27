from django.contrib import admin
from projects.models.UserProjectPermissions import UserProjectPermissions

@admin.register(UserProjectPermissions)
class UserProjectPermissionsAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'projects',
        'can_view',
        'can_edit',
        'can_delete'
    )
    list_filter = ('projects', 'can_edit', 'can_delete')
    search_fields = ('user__username', 'projects__name')
    autocomplete_fields = ('user', 'projects')
