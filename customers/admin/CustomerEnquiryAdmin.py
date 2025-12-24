from django.contrib import admin
from ..models.CustomerEnquiry import CustomerEnquiry
from django.utils.html import format_html
from django.contrib.auth.hashers import make_password
import secrets
      
class CustomerEnquiryAdmin(admin.ModelAdmin):

    list_display = [ "name", "project_id", "phone_no", "email", "requirement", "budget_min", "notes", "follow_up_date", "notes", "status", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at')       # Remove from FORM
    

admin.site.register(CustomerEnquiry,CustomerEnquiryAdmin)
