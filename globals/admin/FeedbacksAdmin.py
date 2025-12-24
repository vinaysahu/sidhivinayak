from django.contrib import admin
from ..models.Feedbacks import Feedbacks
from ..models.Categories import Categories
from common.filters.adminModelFilter import TableForiegnKeyListFilter

class FeedbacksAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    list_display = ["name", "mobile", "message", "category_id", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    list_filter = [TableForiegnKeyListFilter("Category", "category_id", "name", Categories)]
    search_fields = ["name", "mobile"]
    

admin.site.register(Feedbacks,FeedbacksAdmin)
