from django.contrib import admin

from ..models import ChatSession, ChatMessage, PendingTransaction


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "updated_at", "created_at")
    list_filter = ("user",)
    search_fields = ("title", "user__username")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "created_at")
    list_filter = ("role",)
    readonly_fields = ("session", "role", "content", "created_at")
    search_fields = ("session__title",)


@admin.register(PendingTransaction)
class PendingTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "status", "created_transaction", "created_at", "resolved_at")
    list_filter = ("status",)
    readonly_fields = ("session", "payload", "created_transaction", "created_at", "resolved_at")
