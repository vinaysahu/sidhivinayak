from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('user-customer-ledger/', views.user_customer_ledger_report, name='user_customer_ledger'),
    path('user-customer-ledger/pdf/', views.download_report_pdf, name='user_customer_ledger_pdf'),
    path('ajax/projects-for-user/', views.get_projects_for_user, name='ajax_projects_for_user'),
]
