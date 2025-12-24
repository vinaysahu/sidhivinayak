from django.contrib import admin
from ..models.Contacts import Contacts

class ContactsAdmin(admin.ModelAdmin):

    list_display = ["name", "mobile", "alt_mobile", "reg_number", "personal", "type", "status", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM

    list_filter = ["type", "personal","status"]
    search_fields = ["name"]
    

admin.site.register(Contacts,ContactsAdmin)
