from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('user-customer-ledger/', views.user_customer_ledger_report, name='user_customer_ledger'),
    path('user-customer-ledger/pdf/', views.download_report_pdf, name='user_customer_ledger_pdf'),
    path('ajax/projects-for-user/', views.get_projects_for_user, name='ajax_projects_for_user'),
    path('project-expenses/', views.project_expenses_report, name='project_expenses'),
    path('customer-report/', views.customer_report, name='customer_report'),
    path('customer-report/pdf/', views.download_customer_report_pdf, name='customer_report_pdf'),
    path('customer-user-ledger/', views.customer_user_ledger_report, name='customer_user_ledger'),
    path('customer-user-ledger/pdf/', views.download_customer_user_ledger_pdf, name='customer_user_ledger_pdf'),
    path('ajax/customers-for-project/', views.ajax_customers_for_project, name='ajax_customers_for_project'),
]
