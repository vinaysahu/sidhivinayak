from django.contrib import admin
from ..models.Customers import Customers
from django.utils.html import format_html
from django.contrib.auth.hashers import make_password
import secrets
      
class CustomerAdmin(admin.ModelAdmin):

    list_display = [ "username", "show_full_name", "show_image", "email", "phone_no", "alt_phone_no", "address", "status", "created_at", "updated_at" ] # grid mae kaisa view
    exclude = ('created_at', 'updated_at','auth_key', 'password_hash', 'password_reset_token')       # Remove from FORM


    def show_full_name(self, obj):
        if obj.first_name and obj.last_name:
            return obj.first_name+ ""+ obj.last_name
        return obj.first_name
    show_full_name.short_description = "Full Name"
    
    def show_image(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="50" height="50" />', obj.avatar.url)
        return "—"

    show_image.short_description = "Logo"

    list_filter = ["status"]
    search_fields = ["first_name","last_name","username","email","phone_no","alt_phone_no"]

    def save_model(self, request, obj, form, change):

        # 🔹 ONLY for NEW customer
        if not change:

            # 1️⃣ Generate auth_key automatically
            obj.auth_key = secrets.token_hex(16)  # 32 char secure key

            # 2️⃣ Prepare raw password
            if obj.first_name:
                raw_password = f"{obj.first_name}@123"
            else:
                raw_password = f"{obj.username}@123"

            # 3️⃣ Encrypt password
            obj.password_hash = make_password(raw_password)

        super().save_model(request, obj, form, change)
    

admin.site.register(Customers,CustomerAdmin)
