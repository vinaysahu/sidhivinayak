from django.urls import path

from . import views


app_name = "chat"

urlpatterns = [
    path("", views.chat_page, name="chat_page"),
    path("api/sessions/", views.list_sessions, name="list_sessions"),
    path("api/sessions/new/", views.new_session, name="new_session"),
    path("api/sessions/<int:session_id>/", views.get_session, name="get_session"),
    path("api/sessions/<int:session_id>/send/", views.send_message, name="send_message"),
    path("api/pending/<int:pending_id>/confirm/", views.confirm_pending, name="confirm_pending"),
    path("api/pending/<int:pending_id>/cancel/", views.cancel_pending, name="cancel_pending"),

    # Inline-form endpoints (no AI involved)
    path("api/lookup/customers/", views.lookup_customers, name="lookup_customers"),
    path("api/lookup/users/", views.lookup_users, name="lookup_users"),
    path("api/lookup/customer-ledgers/", views.lookup_customer_ledgers, name="lookup_customer_ledgers"),
    path("api/quick/customer-txn/", views.quick_create_customer_txn, name="quick_create_customer_txn"),
    path("api/translate/", views.translate_text, name="translate_text"),

    # Project Workers chatbot endpoints
    path("api/worker-types/", views.get_worker_types, name="get_worker_types"),
    path("api/create-worker/", views.create_global_worker, name="create_global_worker"),
    path("api/project-search/", views.project_search, name="project_search"),
    path("api/projects/<int:project_id>/unassigned-workers/", views.project_unassigned_workers, name="project_unassigned_workers"),
    path("api/projects/<int:project_id>/assign-workers/", views.project_assign_workers, name="project_assign_workers"),
    path("api/projects/<int:project_id>/workers/<int:wages_type>/", views.project_workers_by_wages_type, name="project_workers_by_wages_type"),
    path("api/projects/<int:project_id>/mark-attendance/", views.mark_per_day_attendance, name="mark_per_day_attendance"),
    path("api/pay-per-day/", views.pay_per_day_workers, name="pay_per_day_workers"),
    path("api/project-workers/<int:pw_id>/detail/", views.project_worker_detail, name="project_worker_detail"),
    path("api/project-workers/<int:pw_id>/lum-sum-pay/", views.lum_sum_pay, name="lum_sum_pay"),
    path("api/project-workers/<int:pw_id>/per-hour-pay/", views.per_hour_pay, name="per_hour_pay"),
    path("api/project-workers/<int:pw_id>/per-sqft-pay/", views.per_sqft_pay, name="per_sqft_pay"),

    # Project Suppliers chatbot endpoints
    path("api/brands/", views.get_brands, name="get_brands"),
    path("api/create-supplier/", views.create_global_supplier, name="create_global_supplier"),
    path("api/suppliers/", views.supplier_search, name="supplier_search"),
    path("api/projects/<int:project_id>/supplier-ledgers/", views.project_supplier_ledgers, name="project_supplier_ledgers"),
    path("api/projects/<int:project_id>/create-supplier-ledger/", views.create_project_supplier_ledger, name="create_project_supplier_ledger"),
    path("api/supplier-ledgers/<int:ledger_id>/", views.supplier_ledger_detail, name="supplier_ledger_detail"),
    path("api/supplier-ledgers/<int:ledger_id>/add-payment/", views.add_supplier_payment, name="add_supplier_payment"),

    # User Ledger chatbot endpoints
    path("api/all-users/", views.all_users_list, name="all_users_list"),
    path("api/user-ledgers/", views.user_ledger_list, name="user_ledger_list"),
    path("api/create-user-ledger/", views.create_user_ledger, name="create_user_ledger"),
    path("api/user-ledgers/<int:ledger_id>/", views.user_ledger_detail, name="user_ledger_detail"),
    path("api/user-ledgers/<int:ledger_id>/add-transaction/", views.add_user_ledger_transaction, name="add_user_ledger_transaction"),

    # Context-aware smart form endpoints
    path("api/parse-context/", views.parse_context, name="parse_context"),
    path("api/customer-ledger-for-project/", views.customer_ledger_for_project, name="customer_ledger_for_project"),
    path("api/project-houses/", views.project_houses_list, name="project_houses_list"),
    path("api/create-customer-ledger-chatbot/", views.create_customer_ledger_chatbot, name="create_customer_ledger_chatbot"),
    path("api/customer-ledger-chatbot/<int:ledger_id>/", views.customer_ledger_chatbot_detail, name="customer_ledger_chatbot_detail"),
    path("api/customer-ledger-chatbot/<int:ledger_id>/add-transaction/", views.add_customer_ledger_transaction, name="add_customer_ledger_transaction"),
    path("api/user-ledgers-for-creditor/", views.user_ledgers_for_creditor, name="user_ledgers_for_creditor"),
]
